#ATH fyrst þarf að keyra
#ssh-copy-id nemandi@raspi3.rhi.hi.is
##Keyra shell script inn í folder þarf sem þú vilt savea niðurstöður
#Til að keyra: sh SaekjaGraf.sh
#Keyrsla fer inn í raspi tölvu, sækir graf og vistar á tölvuna þína og opnar
#það graf.
#ssh nemandi@raspi2.rhi.hi.is
scp nemandi@raspi3.rhi.hi.is:nidurstodur.png .
open nidurstodur.png
