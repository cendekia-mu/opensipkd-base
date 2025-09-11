from http.client import NOT_FOUND


SUCCESS = {
    "error": {
        "code": "0000",
        "msg": "Data sudah dibayar"
    }
}

ALLREADYPAID = {
    "error": {
        "code": "0001",
        "msg": "Data sudah dibayar"
    }
}

PAYMENTMISMATCH = {
    "error": {
        "code": "0002",
        "msg": "Jumlah pembayaran tidak sesuai"
    }
}

NOT_FOUND = {
    "error": {
        "code": "404",
        "msg": "Data Tidak Ditemukan"
    }
}
