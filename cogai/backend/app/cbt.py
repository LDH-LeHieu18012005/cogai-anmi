"""Readiness-led CBT pacing (brief 1.2; figure 7: situation → thought → evidence → balanced view → small action).

The appraisal gates of CARE decide *whether* there is something to work on; the user
decides *whether* to work on it. AnMi moves at most one step per turn, holds back while
distress is high, and returns to listening as soon as the user asks to just talk.
"""
import re

from .research import gates
from .safety import normalize

ORDER = ['listen', 'clarify', 'identify', 'evidence', 'action']
LABELS = {'listen': 'Lắng nghe', 'clarify': 'Làm rõ tình huống', 'identify': 'Nhận diện suy nghĩ',
          'evidence': 'Cân nhắc bằng chứng', 'perspective': 'Thử góc nhìn khác', 'action': 'Chọn một việc nhỏ'}
# The user signals they want to be heard, not worked on.
NOT_READY = [r'\bchi muon (ke|noi|tam su|duoc nghe)', r'\bdung (phan tich|hoi nua|day doi)', r'\bkhong muon (phan tich|lam bai tap|tra loi)',
             r'\bthoi (dung|khong) hoi', r'\bde (minh|em|toi) yen\b', r'\bkhong muon noi ve (chuyen|viec) (do|nay)']
EVIDENCE_TURNS = 2


def not_ready(message):
    text = normalize(message)
    return any(re.search(pattern, text) for pattern in NOT_READY)


def advance(state, appraisal, message, user_turns):
    """Return the step to use on the next turn and update the sticky cues in `state`."""
    current = state.get('step') if state.get('step') in ORDER else 'listen'
    cues = state.setdefault('cues', {'dot': False, 'distortion': False})
    if not_ready(message):
        state['cues'] = {'dot': False, 'distortion': False}
        state['step_turns'] = 0
        return 'listen'
    if appraisal.status == 'available':
        active = gates(appraisal, user_turns)
        cues['dot'] = cues['dot'] or active['dot']
        cues['distortion'] = cues['distortion'] or active['distortion']
        intense = appraisal.fields['affect_intensity'].value == 'high'
    else:
        intense = False
    turns = state.get('step_turns', 0) + 1
    nxt = current
    if intense and current in {'listen', 'clarify'}:
        nxt = current  # Validate first; questioning thoughts in acute distress feels dismissive.
    elif current == 'listen' and cues['dot']:
        nxt = 'clarify'
    elif current == 'clarify' and (cues['distortion'] or turns >= 2):
        nxt = 'identify' if cues['dot'] else 'clarify'
    elif current == 'identify':
        nxt = 'evidence' if cues['distortion'] or turns >= 2 else 'identify'
    elif current == 'evidence' and turns >= EVIDENCE_TURNS:
        nxt = 'action'
    elif current == 'action':
        # One small step chosen: close the cycle and go back to listening.
        nxt = 'listen'
        state['cues'] = {'dot': False, 'distortion': False}
    state['step_turns'] = 0 if nxt != current else turns
    return nxt
