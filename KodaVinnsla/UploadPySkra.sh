#ATH fyrst þarf að keyra
#ssh-copy-id nemandi@raspi3.rhi.hi.is
#vera inn í folder þar sem .py skrá er
#Shell script uploadar .py skrá og keyrir hana
scp SvorunViftu.py nemandi@raspi3.rhi.hi.is:
ssh nemandi@raspi3.rhi.hi.is python3 SvorunViftu.py
