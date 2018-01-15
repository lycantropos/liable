import enum
from itertools import (chain,
                       zip_longest)
from typing import (Any,
                    Iterable,
                    Iterator,
                    Sequence)

import inflect
from nltk.corpus import wordnet

STRINGS_SEPARATOR = ',\n'


class Case(enum.Enum):
    upper = 'UPPER_CASE'
    camel = 'camelCase'
    snake = 'snake_case'


def join(strings: Iterable[str],
         *,
         sep: str = STRINGS_SEPARATOR) -> str:
    return sep.join(strings)


def join_with_wrapping(strings: Sequence[str],
                       *,
                       sep: str = STRINGS_SEPARATOR) -> str:
    if len(strings) == 1:
        string, = strings
        return string
    return '(' + sep.join(strings) + ')'


def wrap_with_quotes(string: str) -> Any:
    quote_character = '"'
    return quote_character + string + quote_character


def to_plurals(string: str,
               *,
               target_case: Case = None) -> str:
    if target_case is None:
        target_case = guess_case(string)
    words = split_words(string)
    pluralized_words = map(to_plural, words)
    return to_case_converters[target_case](pluralized_words)


def guess_case(string: str) -> Case:
    if is_snake_case(string):
        return Case.snake
    elif is_upper_case(string):
        return Case.upper
    elif is_camel_case(string):
        return Case.camel
    else:
        raise ValueError('Cannot guess case for string: "{string}".'
                         .format(string=string))


def split_words(string: str) -> Iterator[str]:
    alphanumeric_string = ''.join(character
                                  if character.isalnum()
                                  else ' '
                                  for character in string)
    result = filter(None, alphanumeric_string.split())
    yield from chain.from_iterable(map(split_camel_case, result))


def split_camel_case(string: str) -> Iterator[str]:
    if not string:
        yield string
        return

    word = string[0]
    for character, next_character in zip_longest(string, string[1:],
                                                 fillvalue=''):
        if character.islower() and next_character.isupper():
            yield word.lower()
            word = ''
        if character.isupper() and next_character.islower():
            # for names like "HTTPResponse"
            # which consists of words "HTTP", "Response"
            previous_word = word[:-1]
            if previous_word:
                yield previous_word.lower()
            word = character + next_character
        else:
            word += next_character
    yield word.lower()


def is_camel_case(string: str) -> bool:
    return (not is_snake_case(string)
            and not is_upper_case(string)
            and all(character.isalnum() for character in string))


def is_snake_case(string: str) -> bool:
    return all(not character.isalpha() or character.islower()
               for character in string)


def is_upper_case(string: str) -> bool:
    return all(not character.isalpha() or character.isupper()
               for character in string)


def to_plural(word: str,
              *,
              engine: inflect.engine = inflect.engine()) -> str:
    is_plural = engine.singular_noun
    if not is_noun(word) or is_plural(word):
        return word
    return engine.plural(word)


def to_upper(words: Iterable[str]) -> str:
    return '_'.join(map(str.upper, words))


def to_camel(words: Iterable[str]) -> str:
    words = iter(words)
    result = next(words).lower()
    for word in words:
        if word.isupper():
            result += word
        else:
            result += word.title()
    return result


def to_snake(words: Iterable[str]) -> str:
    return '_'.join(map(str.lower, words))


to_case_converters = {
    Case.upper: to_upper,
    Case.camel: to_camel,
    Case.snake: to_snake
}


def is_noun(word: str) -> bool:
    synsets = wordnet.synsets(word)
    return any(synset.pos() == wordnet.NOUN
               for synset in synsets)


def iterative_join(*strings: str,
                   sep: str = '') -> Iterator[str]:
    if not strings:
        return
    strings = iter(strings)
    result = next(strings)
    yield result
    for string in strings:
        result = result + sep + string
        yield result
