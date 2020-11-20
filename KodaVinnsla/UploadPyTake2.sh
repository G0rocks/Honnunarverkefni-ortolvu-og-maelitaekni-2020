#ATH fyrst þarf að keyra
#ssh-copy-id nemandi@raspi3.rhi.hi.is
#vera inn í folder þar sem .py skrá er
#Shell script uploadar .py skrá og keyrir hana
scp SvorunViftuTAKE2.py nemandi@raspi5.rhi.hi.is:
ssh nemandi@raspi5.rhi.hi.is python3 SvorunViftuTAKE2.py
