import logging
import sys
import traceback


class LogExceptionsMiddleware:

    def process_exception(self, request, exception):
        traceback.print_exception(*sys.exc_info())
