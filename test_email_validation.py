#!/usr/bin/env python
import unittest, re, sys
from email_validation import valid_email_address

# This is a list of valid email addresses that will be tested. Add more if desired.
VALID_ADDRESSES = ['me@localhost', 'me@example.com', 'my.name@example.com', 'my_hyph-enated.name+label@sub.example.com', '"myname"@this.should.also.work']

# These addresses are all invalid for one reason or another.  Augment as desired.
INVALID_ADDRESSES = ['', 'two@at@signs', 'forgot.at.sign', 'unquoted spaces@example.com']

# Here are test patterns (positive and negative) corresponding to each
# of the pattern components defined in email_validation.  In order to add
# more tests, it is only necessary to edit this dictionary (and/or
# VALID_ADDRESSES above).
TEST_PATTERNS = {('WSP', WSP): {'positive': [' ', '\t'],
                                'negative': ['', '  ', 'a', 'abc', '\r']},
                 ('CRLF', CRLF): {'positive': ['\r\n'],
                                  'negative': ['', '\n', '\r', '\n\r', 'abc']},
                 ('NO-WS-CTL', '[' + NO_WS_CTL + ']'): {'positive': ['\x03', '\x08', '\x12'],
                                                        'negative': ['', '\x00', 'a', '0123']},
                 ('quoted-pair', QUOTED_PAIR): {'positive': ['\\.', r'\.', r'\\'],
                                                'negative': ['', '\\', 'a', '0']},
                 ('FWS', FWS): {'positive': [' ', '\t', '  ', '\t \t', '\r\n ', ' \t \r\n\t'],
                                'negative': ['', '\r\n', '\t\r\n']},
                 ('ctext', CTEXT): {'positive': ['a', '0', '\x07'],
                                    'negative': ['', '(', ')', '\\']},
                 ('ccontent', CCONTENT): {'positive': ['F', '5', '\x08', '\\.', r'\.', r'\\'],
                                          'negative': ['', '(', ')']},
                 ('comment', COMMENT): {'positive': ['(comment)', '( more   c o m m e n t  )', '()', '( )'],
                                        'negative': ['', 'comment', '"comment"', '(comment', '(comment) ']},
                 ('CFWS', CFWS): {'positive': ['(comment)', ' (comment)', '   (comment) ', '(comment) ', '\r\n (comment)\t'],
                                  'negative': ['', '\t\r\n(comment)\t']},
                 ('atext', ATEXT): {'positive': ['r', 'X', '4', '!', '#', '^', '}', '~'],
                                    'negative': ['', '\\', ' ', '\x02', '@']},
                 ('atom', ATOM): {'positive': ['apple', '(pear)banana', 'peach (p_u!m{pk}in)  \t', 'cherry  (plum)', 'my+full+name'],
                                  'negative': ['', 'me@there', 'dot.com']},
                 ('dot-atom-text', DOT_ATOM_TEXT): {'positive': ['myname', 'my.name', 'more.dots.here', 'with_funny!#$.characters.wit|hin'],
                                                    'negative': ['', 'ends.with.dot.', 'hello@there.com', ' (a comment) and.something.else']},
                 ('dot-atom', DOT_ATOM): {'positive': ['(comment)followed.by.this', ' (before) and.then.comes (after)', 'even.with\r\n\t(w h i\te space)'],
                                          'negative': ['', 'not@at-signs.though']},
                 ('qtext', QTEXT): {'positive': ['\x08', 'D', '+'],
                                    'negative': ['', '\r', '"']},
                 ('qcontent', QCONTENT): {'positive': ['\x06', ',', '&', 'a', r'\"'],
                                          'negative': ['', '\x09', '"']},
                 ('quoted-string', QUOTED_STRING): {'positive': ['"string"', '""', '" "', '"string with spaces!"', '(comment) "then the string"'],
                                                    'negative': ['', 'noquote', '"missing start quote', 'missing end quote"']},
                 ('local-part', LOCAL_PART): {'positive': ['something', '"something.quoted"', '"something with spaces"'],
                                              'negative': ['', '"mismatched.quotes', 'no@signsyet.please']},
                 ('dtext', DTEXT): {'positive': ['\x02', 'h', '(', '|'],
                                    'negative': ['', '\x09', ']', '\\']},
                 ('dcontent', DCONTENT): {'positive': ['\x01', 'I', '(', '\\[', r'\\'],
                                          'negative': ['', '\n', '[']},
                 ('domain-literal', DOMAIN_LITERAL): {'positive': ['[literal]', '(comment)[literal]', ' (s p ace) [lit eral]', '[something] (comment)'],
                                                      'negative': ['', 'nobracket', '[missingone', '(co mme nt) missing bracket]']},
                 ('domain', DOMAIN): {'positive': ['domain.name', 'a.longer.domain.name', '(comment)[stuff in brackets]', '(comment) [bracketed text]'],
                                      'negative': ['', '[bracketed text]domain.name']},
                 ('addr-spec', ADDR_SPEC): {'positive': VALID_ADDRESSES,
                                            'negative': INVALID_ADDRESSES}}

# It's boring to specify loads of test_xxxxx methods to check all the
# regexps in the email validation code, but it is necessary to check
# them.  So we use Python's metaclass capabilities to generate and inject
# the needed test methods.
#
# The metaclass approach used here to inject tests was taken from
# https://gist.github.com/852268/e8430a8322c25c39fbd5cd18b84d21d2b26b9be8
class TestEmailValidationMetaclass(type):

    def __new__(cls, name, bases, dct):
        test_index = 0

        for ((token_name, regexp), string_sets) in TEST_PATTERNS.items():
            for string in string_sets['positive']:
                cls.inject_match_test(True, token_name, regexp, string, test_index, dct)
                test_index += 1
            for string in string_sets['negative']:
                cls.inject_match_test(False, token_name, regexp, string, test_index, dct)
                test_index += 1

        cls.inject_valid_tests(dct)
        cls.inject_invalid_tests(dct)

        return super(TestEmailValidationMetaclass, cls).__new__(cls, name, bases, dct)

    @classmethod
    def inject_match_test(cls, should_match, token_name, regexp, string, index, dct):
        """Define a method named "test_[index]" that asserts
        a positive or negative match (depending on value of should_match)
        of regexp for string."""

        assertion = ('assertRegexpMatches' if should_match else 'assertNotRegexpMatches')

        def match_test(self):
            self.longMessage = True
            getattr(self, assertion)(string, '^' + regexp + '$', '(attempting to match ' + token_name + ')')

        dct['test_%03d' % index] = match_test

    @classmethod
    def inject_valid_tests(cls, dct):
        """Define methods named "test_valid_[index]" that test the valid_email_address()
        method with valid addresses."""

        index = 0
        for address in VALID_ADDRESSES:
            def match_test(self):
                self.longMessage = True
                self.assertTrue(valid_email_address(address))

            dct['test_valid_%03d' % index] = match_test
            index += 1

    @classmethod
    def inject_invalid_tests(cls, dct):
        """Define methods named "test_valid_[index]" that test the valid_email_address()
        method with *invalid( addresses."""

        index = 0
        for address in INVALID_ADDRESSES:
            def match_test(self):
                self.longMessage = True
                self.assertFalse(valid_email_address(address))

            dct['test_invalid_%03d' % index] = match_test
            index += 1

class TestEmailValidation(unittest.TestCase):

    # Inject the test methods.
    __metaclass__ = TestEmailValidationMetaclass

if __name__ == '__main__':
    unittest.main()
