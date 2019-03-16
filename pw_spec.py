import logging
import json

log = logging.getLogger(__name__)
log.setLevel(logging.WARN)

class iterfromrule:
  def __init__(self, rulefilename):
    self.rules, self.states = self._read_rulefile(rulefilename)
    self.statesIdx = 0 # Point to current state machine in states
    self.avoids = {} # A dictionary of statesIdx->stateIdx->set(AVOID_CHARACTERS)

  def __iter__(self):
    return self

  def next(self):
    # All state machines are terminated
    if not self.states:
      raise StopIteration

    value = self._getStateValue()

    # Advance current state
    if not self._nextState():
      del self.states[self.statesIdx]

    # Switch to other state machine
    if self.states:
      self.statesIdx = (self.statesIdx-1) % len(self.states)

    return value

  def _getStateValue(self):
    curState = self.states[self.statesIdx]
    value=[]
    for stateIdx, stateVal in enumerate(curState):
      value.append(self.rules[stateIdx][stateVal])
    return ''.join(value)

  def _nextState(self):
    curState = self.states[self.statesIdx]
    curAvoid = self.avoids.setdefault(self.statesIdx,{})
    myQueue = [(len(self.rules)-1, 1)]
    while myQueue:
      ruleIdx, stateChg = myQueue.pop()
      if ruleIdx>=len(self.rules): 
        continue
      if ruleIdx<0: 
        return False
      curAvoid.pop(ruleIdx, None)

      ruleSet  = self.rules[ruleIdx]
      stateVal = curState[ruleIdx]
      avoidSet = curAvoid.get(ruleIdx-1, set())

      while True:
        stateVal = (stateVal+stateChg)%len(ruleSet)
        if stateVal==0 and stateChg!=0:
          myQueue.append((ruleIdx-1, 1))
          break
        curRuleVal=ruleSet[stateVal]
        if curRuleVal == '':
          curAvoid[ruleIdx]=avoidSet | set(ruleSet) - {''}
          myQueue.append((ruleIdx+1, 0))
          log.debug("Avoid[%d]=%s",ruleIdx, curAvoid[ruleIdx])
          break
        if curRuleVal not in avoidSet:
          break
        stateChg = 1

      curState[ruleIdx] = stateVal
    log.debug(0, "curState=%s",curState)
    return True

  def save_state(self, filename):
    log.debug("Saving current state into %s...", filename)
    with open(filename, 'w') as f:
      for rule in self.rules:
        f.write(self._genRuleLine(rule))
        f.write('\n')

      for state in self.states:
        f.write('\n')
        f.write(json.dumps(state))

  @classmethod
  def _read_rulefile(cls, rulefilename):
    log.debug("Processing rule file %s...", rulefilename)
    lineCnt=0

    with open(rulefilename, 'r') as f:
      # Read password rules
      rules=[]
      for line in f:
        lineCnt += 1
        rule = cls._parseRuleLine(line)

        #Stop at the empty line where password rule should be ended
        if not rule:
          break

        rules.append(rule)
        log.debug("  [%s:%d] - %s", rulefilename, lineCnt, rule)

      # Read next search state(s)
      states = []
      for line in f:
        lineCnt +=1
        state = json.loads(line)

        #Stop at the empty line where state(s) should be ended
        if not state:
          break

        if len(state) != len(rules):
          log.warn("expected state length is %d, but got %d"
              , len(rules), len(state))
          # Extend state
          while len(state)<len(rules): state.append(0)

          # Truncate state
          while len(state)>len(rules): state.pop()

        states.append(state)

      if not states:
        states.append([0]*len(rules))

    return rules, states

  @staticmethod
  def _parseRuleLine(line):
      """Parse a line of rule for a password letter

      Using \ for escape any special control characters. Following are
      special control characters:
      $ - password letter can be empty or skip
      # - will be use as inline comment
      """
      escape=''
      charSet=set()
      charList=[]

      for c in line:
        if c in ('\n', '\r'):
          continue
        elif escape: 
          cc = c
          escape=''
        elif c == '#':
        # Ignore inline commenting
          break
        elif c == '\\':
          escape=c
          continue
        elif c == '$':
          cc = ''
        else:
          cc = c

        if cc not in charSet:
          charSet.add(cc)
          charList.append(cc)

      if escape and (escape not in charSet):
        charSet.add(escape)
        charList.append(escape)

      return charList 

  @staticmethod
  def _genRuleLine(rule):
      """Generate rule line for a password letter

      Using \ for escape any special control characters. Following are
      special control characters:
      $ - password letter can be empty or skip
      # - will be use as inline comment
      """
      line = []
      for r in rule:
        if r == '':
          line.append('$')
        elif r == '$': 
          line.append('\\$')
        else: 
          line.append(r)
      return ''.join(line)

#  @staticmethod
#  def _parseStateLine(line):
#      """Parse a state line 
#
#      Using \ for escape any special control characters. Following are
#      special control characters:
#      , - state separator
#      # - will be use as inline comment
#      """
#      escape=''
#      states=[]
#
#      for c in line:
#        if c in ('\n', '\r'):
#          continue
#        elif escape: 
#          cc = c
#          escape=''
#        elif c == '#':
#        # Ignore inline commenting
#          break
#        elif c == '\\':
#          escape=c
#          continue
#        elif c == ',':
#          states.append('')
#          continue
#        else:
#          cc = c
#
#        states[-1] = states[-1] + cc
#
#      if escape and (escape not in charSet):
#        states[-1] = states[-1] + escape
#
#      return map(int, states)

