
header ="""
   JENIS GAJI : {jenis_gaji}
   BULAN      : {bulan}
   KODE UNIT  : {unit_kd}
   UNIT KERJA : {unit_nm}
   +----+------------------------------+-----+---------------------------------+---------------------+---------------+------+
   |    |                              | STA |     P E N G H A S I L A N       |    P O T O N G A N  |               |      |
   |    |                              |KAWIN|-----------+----------+----------+----------+----------|               |      |
   |    |            NAMA              |     |GAPOK      |-T.UMUM   |-T.PPH    |-PFK.BULOG|-I.ASKES  |   JUMLAH      |      |
   |NO. |         NIP.PEGAWAI          | JML |TUNJ. KEL  |-T.STRUK  |-I.ASKES  |-IWP.     |-I.JKK/JKM|  PENGHASILAN  |TANDA |
   |URUT|    STATUS PEG. (PNS/CPNS)    |ANAK/|a.IST/SUAMI|-T.FUNGS  |-I.JKK/JKM|-TAPERUM  |-LAIN-LAIN|  BERSIH YANG  |TANGAN|
   |    |                              |JIWA |b.ANAK     |-T.TMBH.UM|-P BULAT  |-PPH.PS.21|          |  DIBAYARKAN   |      |
   |    |                              |     |           |-T.BERAS  |JML.KOTOR |-SEWA RMH |JML.POTNGN|               |      |
   |----+------------------------------+-----+-----------+----------+----------+----------+----------+---------------+------|
   |  1 |              2               |  3  |    4      |    5     |    6     |    7     |    8     |      9        |  10  |
   |----+------------------------------+-----+-----------+----------+----------+----------+----------+---------------+------|
"""

   +----+------------------------------+-----+---------------------------------+---------------------+---------------+------+
   |{no}|{nama}                        |     |GAPOK      |-T.UMUM   |-T.PPH    |-PFK.BULOG|-I.ASKES  |   JUMLAH      |      |
   |    |{nip} {tgl_lahir}             | JML |TUNJ. KEL  |-T.STRUK  |-I.ASKES  |-IWP.     |-I.JKK/JKM|  PENGHASILAN  |TANDA |
   |    |{peg_st}/{peg_kd}.{peg_tm}    | NAK/|a.IST/SUAMI|-T.FUNGS  |-I.JKK/JKM|-TAPERUM  |-LAIN-LAIN|  BERSIH YANG  |TANGAN|
   |    |{gol_kd} - {gol_nm}           |JIWA |b.ANAK     |-T.TMBH.UM|-P BULAT  |-PPH.PS.21|          |  DIBAYARKAN   |      |
   |    |MKG: {mk} Thn,{th} Bln.{bl}   |     |           |-T.BERAS  |JML.KOTOR |-SEWA RMH |JML.POTNGN|               |      |
   |----+------------------------------+-----+-----------+----------+----------+----------+----------+---------------+------|
