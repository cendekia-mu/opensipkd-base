class OpensipkdException(Exception):
    code = "-9999"
    message = "Error Aplikasi"
class DataException(OpensipkdException):
    code = "-1000"
    message = "Kesalahan pada data"
class DataValidation(DataException):
    code = "-1001"
    message = "Data tidak valid"
class DataNotFound(DataException):
    code = "-1002"
    message = "Record Not Found"

class DataFound(DataException):
    code = "-1003"
    message = "Data sudah ada"


class UserException(OpensipkdException):
    code = "-2000"
    mesasge = "Kesalahan pada"

class UserNotFound(DataNotFound):
    message = "User Not Found"

