from fastapi import HTTPException
from fastapi import status

class CustomHTTPException(HTTPException):
    def __init__(self, status_code: int = status.HTTP_404_NOT_FOUND, detail: str = "Bulunamadı."):
        super().__init__(status_code=status_code, detail=detail)

class UnauthorizedException(HTTPException):
    def __init__(self, status_code: int = status.HTTP_401_UNAUTHORIZED, detail: str = "Yetkisiz erişim."):
        super().__init__(status_code=status_code, detail=detail)

#Geçersiz istek durumunda kullanılacak özel bir istisna sınıfı
class BadRequestException(HTTPException):
    def __init__(self, status_code: int = status.HTTP_400_BAD_REQUEST, detail: str = "Eksik alan"):
        super().__init__(status_code=status_code, detail=detail)

#Yetkisi var ama erişim yasak
class ForbiddenException(HTTPException):
    def __init__(self, status_code: int = status.HTTP_403_FORBIDDEN, detail: str = "Erişim yasak."):
        super().__init__(status_code=status_code, detail=detail)

#duplicate kayıt
class DuplicateRecordException(HTTPException):
    def __init__(self, status_code: int = status.HTTP_409_CONFLICT, detail: str = "Kayıt zaten mevcut."):
        super().__init__(status_code=status_code, detail=detail)

#Sunucu hatası için özel bir istisna sınıfı
class UnexpectedServerErrorException(HTTPException):
    def __init__(self, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, detail: str = "Format doğru işlenemiyor."):
        super().__init__(status_code=status_code, detail=detail)

#Beklenmeyen hata
class InternalServerErrorException(HTTPException):
    def __init__(self, status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR, detail: str = "Beklenmeyen bir hata oluştu."):
        super().__init__(status_code=status_code, detail=detail)

class UnprocessableEntityException(HTTPException):
    def __init__(self, status_code: int = status.HTTP_422_UNPROCESSABLE_ENTITY, detail: str = "İşlenemeyen varlık."):
        super().__init__(status_code=status_code, detail=detail)