RFC 2822 - style email validation for Python
(c) 2011 Noel Bush <noel@aitools.org>
This code is made available to you under the GNU LGPL v3.

This module provides a single method, valid_email_address(), which returns True or False to indicate whether a given address is valid according to the 'addr-spec' part of the specification given in [RFC 2822](http://www.ietf.org/rfc/rfc2822.txt).  Ideally, we would like to find this in some other library, already thoroughly tested and well- maintained.  The standard Python library email.utils contains a parse_addr() function, but it is not sufficient to detect many malformed addresses.

This implementation aims to be faithful to the RFC, with the exception of a circular definition (see comments inline), and with the omission of the pattern components marked as "obsolete".

Yes, all this really does is build a big regular expression.  But it builds it in nice pieces that correspond to the RFC, and there's a big bunch of unit tests that try to ensure each little piece of the regexp works as intended.  (See test_email_validation.py.)
