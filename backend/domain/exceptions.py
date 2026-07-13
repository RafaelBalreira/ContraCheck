class PDFError(Exception):
    pass


class InvalidPDFError(PDFError):
    pass


class PasswordProtectedError(PDFError):
    pass


class EmptyFileError(PDFError):
    pass


class UnreadablePageError(PDFError):
    pass
