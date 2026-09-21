"""Part A: thread-safe in-memory message queue.

Requirements:
  - FIFO per topic
  - Per-message TTL
  - At-least-once delivery with a visibility timeout
  - Ack semantics (unacked messages are redelivered)

Design notes (the things interviewers look for):
  - Per-topic locks, not one global lock. The manager lock is held only
    long enough to look up/create a topic; all message operations take
    the topic's own lock, so traffic on topic A never blocks topic B.
  - Monotonic clock for all deadlines. Wall clock (time.time) can jump
    (NTP sync, DST); time.monotonic() cannot.
  - Lazy TTL expiry: expired messages are purged when someone touches
    the topic (consume/size), with an eager fallback: an optional
    background sweeper so an idle topic can't grow without bound.
  - Visibility timeout: consume() hides the message instead of deleting
    it. Only ack() deletes. If the consumer dies and never acks, the
    message becomes visible again after the timeout -> at-least-once.
"""

from __future__ import annotations

import threading
import time
import uuid
from collections import deque
from dataclasses import dataclass
from typing import Any, Optional

@dataclass
class Message:
    id: str
    topic: str
    body: Any
    expires_at: Optional[float]      # monotonic deadline, None = no TTL
    delivery_count: int = 0

    def is_expired(self, now: float) -> bool:
        return self.expires_at is not None and now >= self.expires_at

@dataclass
class _InFlight:
    message: Message
    invisible_until: float           # monotonic deadline

class _TopicQueue:
    """One topic: a ready deque (FIFO) + an in-flight table. Own lock."""

    def __init__(self) -> None:
        self.lock = threading.Lock()
        self.ready: deque[Message] = deque()
        self.in_flight: dict[str, _InFlight] = {}

    # -- internal helpers: caller must hold self.lock --------------------

    def _requeue_timed_out(self, now: float) -> None:
        """Visibility timeouts that have lapsed -> back to the ready queue.

        Redelivered messages go to the FRONT: they are the oldest work,
        so this keeps ordering as close to FIFO as at-least-once allows.
        """
        timed_out = [k for k, f in self.in_flight.items()
                     if now >= f.invisible_until]
        # Oldest first so appendleft() preserves their relative order.
        timed_out.sort(key=lambda k: self.in_flight[k].message.delivery_count,
                       reverse=True)
        for key in timed_out:
            flight = self.in_flight.pop(key)
            self.ready.appendleft(flight.message)

    def _purge_expired(self, now: float) -> None:
        """Lazy TTL: drop expired messages from the front of the queue.

        Expired messages deeper in the deque are caught when they reach
        the front, or by the sweeper (eager fallback).
        """
        while self.ready and self.ready[0].is_expired(now):
            self.ready.popleft()

    def _sweep(self, now: float) -> None:
        """Eager fallback: full purge, used by the background sweeper."""
        self.ready = deque(m for m in self.ready if not m.is_expired(now))
        for key in [k for k, f in self.in_flight.items()
                    if f.message.is_expired(now)]:
            del self.in_flight[key]

class MessageQueue:
    def __init__(self, sweep_interval: Optional[float] = None) -> None:
        self._topics: dict[str, _TopicQueue] = {}
        self._topics_lock = threading.Lock()   # guards the dict only
        self._closed = threading.Event()
        if sweep_interval:
            t = threading.Thread(
                target=self._sweeper, args=(sweep_interval,), daemon=True
            )
            t.start()

    def _topic(self, name: str) -> _TopicQueue:
        with self._topics_lock:
            q = self._topics.get(name)
            if q is None:
                q = self._topics[name] = _TopicQueue()
            return q

    # -- public API ------------------------------------------------------

    def publish(self, topic: str, body: Any,
                ttl: Optional[float] = None) -> str:
        """Enqueue a message; returns its id. ttl is seconds from now."""
        now = time.monotonic()
        msg = Message(
            id=uuid.uuid4().hex,
            topic=topic,
            body=body,
            expires_at=(now + ttl) if ttl is not None else None,
        )
        q = self._topic(topic)
        with q.lock:
            q.ready.append(msg)
        return msg.id

    def consume(self, topic: str,
                visibility_timeout: float = 30.0) -> Optional[Message]:
        """Pop the oldest visible, unexpired message, or None.

        The message is NOT removed: it becomes invisible for
        `visibility_timeout` seconds. Ack it before that or it is
        redelivered (at-least-once).
        """
        q = self._topic(topic)
        now = time.monotonic()
        with q.lock:
            q._requeue_timed_out(now)   # dead consumers' work first
            q._purge_expired(now)       # lazy TTL on consume
            if not q.ready:
                return None
            msg = q.ready.popleft()
            msg.delivery_count += 1
            q.in_flight[msg.id] = _InFlight(
                message=msg,
                invisible_until=now + visibility_timeout,
            )
            return msg

    def ack(self, topic: str, message_id: str) -> bool:
        """Confirm processing; True if the ack landed.

        False means the id is unknown OR its visibility timeout already
        lapsed and it went back on the queue — the caller's work may be
        (or may get) done twice. That is the at-least-once contract.
        """
        q = self._topic(topic)
        now = time.monotonic()
        with q.lock:
            flight = q.in_flight.get(message_id)
            if flight is None or now >= flight.invisible_until:
                return False
            del q.in_flight[message_id]
            return True

    def size(self, topic: str) -> dict[str, int]:
        """Counts after purging: {'visible': n, 'in_flight': m}."""
        q = self._topic(topic)
        now = time.monotonic()
        with q.lock:
            q._requeue_timed_out(now)
            q._sweep(now)
            return {"visible": len(q.ready), "in_flight": len(q.in_flight)}

    # -- eager TTL fallback ---------------------------------------------

    def _sweeper(self, interval: float) -> None:
        while not self._closed.wait(interval):
            now = time.monotonic()
            with self._topics_lock:
                topics = list(self._topics.values())
            for q in topics:            # never holds two locks at once
                with q.lock:
                    q._requeue_timed_out(now)
                    q._sweep(now)

    def close(self) -> None:
        self._closed.set()

# ---------------------------------------------------------------------------
# Sanity tests / demo
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    mq = MessageQueue()

    # FIFO per topic
    for i in range(3):
        mq.publish("orders", f"order-{i}")
    got = [mq.consume("orders").body for _ in range(3)]
    assert got == ["order-0", "order-1", "order-2"], got
    print("FIFO per topic          ok:", got)

    # Ack removes; second ack fails
    mid = mq.publish("orders", "order-3")
    msg = mq.consume("orders")
    assert mq.ack("orders", msg.id) is True
    assert mq.ack("orders", msg.id) is False
    print("ack semantics           ok")

    # Visibility timeout -> redelivery, delivery_count bumps
    mq.publish("jobs", "flaky-job")
    first = mq.consume("jobs", visibility_timeout=0.1)
    assert mq.consume("jobs") is None          # invisible while in flight
    time.sleep(0.15)
    again = mq.consume("jobs", visibility_timeout=5)
    assert again is not None and again.id == first.id
    assert again.delivery_count == 2
    assert mq.ack("jobs", first.id) is True    # ack the redelivery
    print("visibility/redelivery   ok")

    # Late ack (after timeout) is rejected
    mq.publish("jobs", "slow-consumer")
    m = mq.consume("jobs", visibility_timeout=0.05)
    time.sleep(0.1)
    assert mq.ack("jobs", m.id) is False
    print("late ack rejected       ok")

    # TTL expiry (lazy, on consume)
    mq.publish("ephemeral", "gone", ttl=0.05)
    mq.publish("ephemeral", "kept")
    time.sleep(0.1)
    m = mq.consume("ephemeral")
    assert m.body == "kept"
    print("lazy TTL on consume     ok")

    # Topics are independent + thread hammering
    import concurrent.futures as cf

    N, WORKERS = 2000, 8
    for i in range(N):
        mq.publish("hammer", i)
    seen: list[int] = []
    seen_lock = threading.Lock()

    def worker() -> None:
        while True:
            m = mq.consume("hammer", visibility_timeout=10)
            if m is None:
                return
            with seen_lock:
                seen.append(m.body)
            assert mq.ack("hammer", m.id)

    with cf.ThreadPoolExecutor(WORKERS) as ex:
        list(ex.map(lambda _: worker(), range(WORKERS)))
    assert sorted(seen) == list(range(N))      # every message exactly once here
    assert mq.size("hammer") == {"visible": 0, "in_flight": 0}
    print(f"concurrency ({WORKERS} threads)  ok: {N} msgs, no loss, no dupes")

    print("\nall checks passed")
