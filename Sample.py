# Initialize.
stringLength = 0;
original = [];
used = [];
permuted = [];
def init(s):
 for i in range(0, len(s)):
  original.append(s[i]);
  used.append(0);
  permuted.append(' ');
 return len(s);

# Factorial.
factorial = [];
def findFactorials():
 factorial.append(1); 
 factorial.append(1);
 for i in range(2, 1005): 
  factorial.append(factorial[i - 1] * i);
  
def nCr(n, r):
 return factorial[n] / (factorial[n - r] * factorial[r]);

# [1]: Last element of the list.
def findLast(l):
 n = len(l);
 if n > 0: return l[n - 1]
 else: return -1

# [2]: Last but one element of the list.
def lastButOne(l):
 n = len(l);
 if n > 1: return l[n - 2]
 else: return -1
 
# [3]: Reverse the list.
def reverseList(l):
 n = len(l)
 for i in range(n - 1, -1, -1): l.append(l[i])
 for i in range(n - 1, -1, -1): l.pop(0)
 
# [4]: Eliminate consecutive duplicates of list elements.
def eliminateDuplicates(l):
 n = len(l)  
 if n == 0: return; 
 j = 1
 previous = l[0]; 
 for i in range(1, n):
  if l[j] == previous: 
   l.pop(j);
   j -= 1
  else: 
   previous = l[j];
  j += 1
  n = len(l)
 
# [5]: Duplicate the elements of a list a given number of times.
def duplicateN1(l1, n):
 l2 = []
 for i in range(0, len(l1)):
  for j in range (0, n):
   l2.append(l1[i]);
 del l1[:];   
 for i in range(0, len(l2)):
  l1.append(l2[i]);
 
# [6]: Drop every n'th element from the list.
def dropNth(l, k):
 n = len(l)
 for i in range(1, n + 1):
  if i % k != 0:
   l.append(l[i - 1])
   
 for i in range(0, n):
  l.pop(0)
  
# [7]: Extract a slice from the list.
def extractSlice(l, left, right):
 rangeCount = right - left + 1
 j = 0
 for i in range(0, rangeCount):
  l.pop(left - 1)
  
# [9]: Sum of all multiples of 3 or 5 below 1000.
def multiplesSum(n):
 sum = 0;
 for i in range(1, n):
  if(i % 3 == 0 or i % 5 == 0): sum += i;             
 print sum;
 
# [10]: English number words.
def fullWords(number):
 n = number;
 l = [];
 M = { 1:"one", 2:"two", 3:"three", 4:"four", 5:"five", 6:"six", 7:"seven", 8:"eight", 9:"nine", 0:"zero" };    
 while(n > 0):
  digit = n % 10;
  l.append(M[digit]);
  n = n / 10;    
 l.reverse();
 s = l[0]
 for i in range(1, len(l)):
  s = s + "-" + l[i];
 print s;
 
# [11]: Lattice Paths.
def latticePaths(n1, m1):
 if(n1 >= m1): print nCr(n1 + m1 - 2, m1 - 1);
 else: print nCr(n1 + m1 - 2, n1 - 1); 
 
# [12]: Lexicographic permutations of a string.
def permuteString(depth):
 if(depth == stringLength):
  s0 = "";
  for i in range(0, stringLength):
   s0 = s0 + permuted[i];
  print s0;
 else:
  for i in range(0, stringLength):
   if used[i] == 0:
    used[i] = 1;
    permuted[depth] = original[i];
    permuteString(depth + 1);
    used[i] = 0;
 
#l = [1, 2, 3, 4, 5, 6, 7]
#fullWords(77)

#findFactorials();
#latticePaths(21, 21);

stringLength = init("123");
permuteString(0);
