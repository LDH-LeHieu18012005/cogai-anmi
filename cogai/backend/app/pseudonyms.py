"""Replace people's names with stable placeholders before text reaches an AI provider.

Brief 1.3 step 1 (figure 2: "tổ trưởng Hùng" -> "[NGƯỜI 1]"). There is no Vietnamese
NER model here, so this is a rule-based pass: a kinship word or job title followed by
capitalised words, or a common surname followed by capitalised words. It lowers, not
removes, identifiability: a bare name at the start of a sentence is not caught.
"""
import re
from contextvars import ContextVar
from .identity import ASSISTANT_NAME

# Mapping for the current request: real name -> placeholder. Inherited by child tasks.
current: ContextVar[dict | None] = ContextVar('cogai_pseudonyms', default=None)

TITLES = ('tổ trưởng', 'tổ phó', 'trưởng ca', 'chuyền trưởng', 'quản đốc', 'quản lý', 'trưởng phòng', 'phó phòng',
          'giám đốc', 'giám sát', 'trưởng nhóm', 'lớp trưởng', 'thầy giáo', 'cô giáo', 'giảng viên', 'bạn trai',
          'bạn gái', 'người yêu', 'anh', 'chị', 'em', 'cô', 'chú', 'bác', 'ông', 'bà', 'thầy', 'cậu', 'dì', 'mợ',
          'dượng', 'bạn', 'sếp', 'con', 'cháu')
SURNAMES = {'Nguyễn', 'Trần', 'Lê', 'Phạm', 'Hoàng', 'Huỳnh', 'Phan', 'Vũ', 'Võ', 'Đặng', 'Bùi', 'Đỗ', 'Hồ', 'Ngô',
            'Dương', 'Lý', 'Đinh', 'Trịnh', 'Đoàn', 'Lâm', 'Tạ', 'Lưu', 'Chu', 'Lương', 'Trương', 'Quách', 'Vương', 'Đào', 'Kiều'}
# Capitalised words that are never people here. Given names that are also parts of
# place names (Minh, Nam, Hà...) are handled by removing whole place phrases first.
# Keep the former assistant name excluded for conversations saved before the rename.
NOT_NAMES = {ASSISTANT_NAME, 'Mầm', 'CogAI', 'AI', 'PHQ', 'GAD', 'KCN', 'Tết', 'Zalo', 'Facebook', 'Google', 'Chủ', 'Nhật', 'Thứ',
             'Việt', 'Trung', 'Thu', 'Xuân', 'Hạ', 'Đông'}
PLACES = ('Hồ Chí Minh', 'Hà Nội', 'Hưng Yên', 'Việt Nam', 'Đà Nẵng', 'Sài Gòn', 'Hải Phòng', 'Bắc Ninh', 'Hải Dương',
          'Thái Bình', 'Nam Định', 'Hà Nam', 'Phố Nối', 'Thăng Long', 'Mỹ Hào', 'Văn Lâm', 'Bình Dương', 'Đồng Nai')
WORD = r'[^\W\d_]+'
# Zero-width lookahead so overlapping candidates ("em bị tổ trưởng Hùng") are all seen.
TITLE_NAME = re.compile(r'(?=\b(?i:' + '|'.join(sorted(map(re.escape, TITLES), key=len, reverse=True))
                        + r')\s+(' + WORD + r'(?:\s+' + WORD + r'){0,3}))')
SURNAME_NAME = re.compile(r'(?=\b(' + WORD + r'(?:\s+' + WORD + r'){1,3}))')


def capitalised_run(words):
    """Leading run of capitalised words that are not on the exclusion list."""
    run = []
    for word in words:
        if not word[:1].isupper() or word in NOT_NAMES:
            break
        run.append(word)
    return run


def find_names(text):
    for place in PLACES:
        text = text.replace(place, 'nơi')
    names = []
    for match in TITLE_NAME.finditer(text):
        run = capitalised_run(match.group(1).split())
        if run:
            names.append(' '.join(run))
    for match in SURNAME_NAME.finditer(text):
        words = match.group(1).split()
        if words[0] in SURNAMES:
            run = [words[0]] + capitalised_run(words[1:])
            if len(run) >= 2:
                names.append(' '.join(run))
    return names


def build(texts):
    mapping = {}
    for text in texts:
        for name in find_names(text):
            if name in mapping:
                continue
            # "Tú" after "Nguyễn Văn Tú" is the same person and shares the placeholder.
            same = next((known for known in mapping if ' ' in known and known.split()[-1] == name), None)
            mapping[name] = mapping[same] if same else f'[NGƯỜI {len(set(mapping.values())) + 1}]'
    return mapping


def mask(text, mapping=None):
    mapping = current.get() if mapping is None else mapping
    if not mapping or not isinstance(text, str):
        return text
    # Shield place names so "anh Minh" never turns "Hồ Chí Minh" into a placeholder.
    shielded = {f'\x00{i}\x00': place for i, place in enumerate(PLACES)}
    for key, place in shielded.items():
        text = text.replace(place, key)
    for name in sorted(mapping, key=len, reverse=True):
        text = re.sub(r'(?<!\w)' + re.escape(name) + r'(?!\w)', mapping[name], text)
    for key, place in shielded.items():
        text = text.replace(key, place)
    return text


def unmask(value, mapping=None):
    """Restore names in model output, recursively through JSON-like structures."""
    mapping = current.get() if mapping is None else mapping
    if not mapping:
        return value
    if isinstance(value, str):
        for name, token in mapping.items():
            value = value.replace(token, name)
        return value
    if isinstance(value, list):
        return [unmask(v, mapping) for v in value]
    if isinstance(value, dict):
        return {k: unmask(v, mapping) for k, v in value.items()}
    return value
