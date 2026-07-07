#!/usr/bin/env python3
"""Generate a random real device identity. Output: shell-sourceable vars file."""
import json, random, string, hashlib, time, sys, os

tac_db_path = sys.argv[1]
idx_arg = sys.argv[2] if len(sys.argv) > 2 else 'random'
out_file = sys.argv[3] if len(sys.argv) > 3 else '/tmp/device_vars.sh'

with open(tac_db_path) as f:
    tac_db = json.load(f)

idx = random.randint(0, len(tac_db)-1) if idx_arg == 'random' else int(idx_arg) % len(tac_db)
device = tac_db[idx]
brand = device['brand']
model_name = device['model_name']
tacs = device['tacs']

def gen_imei(tac):
    serial = ''.join([str(random.randint(0,9)) for _ in range(6)])
    partial = str(tac) + serial
    total = 0
    for i, d in enumerate(reversed(partial)):
        n = int(d)
        if i % 2 == 0: n *= 2
        if n > 9: n -= 9
        total += n
    return partial + str((10 - (total % 10)) % 10)

imei1 = gen_imei(random.choice(tacs))
imei2 = gen_imei(random.choice(tacs))
serial = ''.join(random.choices(string.ascii_uppercase + string.digits, k=11))
android_id = hashlib.sha256(f"{time.time_ns()}{random.random()}".encode()).hexdigest()[:16]
gaid = '-'.join([hashlib.md5(f"{time.time_ns()}{i}".encode()).hexdigest()[:x] for i,x in enumerate([8,4,4,4,12])])

ouis = {'Samsung':['8C:F5:A3','B0:72:BF','AC:5F:3E'],'Xiaomi':['28:6C:07','64:CC:2E'],'OPPO':['2C:4D:54','A4:50:46'],'Realme':['2C:4D:54','E8:FB:1C'],'Google':['3C:28:6D','F4:F5:D8'],'TECNO':['D8:1E:05','48:A4:72'],'POCO':['28:6C:07','DC:D8:7D'],'Motorola':['B4:F1:DA','80:6C:1B'],'Vivo':['C8:F8:6D','70:78:8B'],'Oneplus':['94:65:2D','C0:EE:FB'],'Huawei':['FC:48:EF','48:DB:50'],'Nokia':['A4:4E:31','8C:90:D3'],'Infinix':['D8:1E:05','C4:AD:34']}
oui = random.choice(ouis.get(brand, ouis.get(brand.capitalize(), ['00:1A:2B'])))
wifi_mac = oui + ':' + ':'.join([f'{random.randint(0,255):02x}' for _ in range(3)])
bt_mac = oui + ':' + ':'.join([f'{random.randint(0,255):02x}' for _ in range(3)])

android_ver = random.choice(['13','14'])
build_id = random.choice(['TP1A.220624.014','UP1A.231005.007','UKQ1.230804.001','AP2A.240805.005'])
device_code = model_name.replace(' ','_').lower()[:10]
build_num = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
fp = f"{brand.lower()}/{device_code}/{device_code}:{android_ver}/{build_id}/{build_num}:user/release-keys"
density = random.choice([396,400,420,440,480])
baseband = random.choice(['G991BXXS7EWBA','MPSS.HI.2.0.c8','MOLY.LR13.R1.MP.V238','g5300q-230920'])
hw = random.choice(['qcom','exynos2400','mt6985','mt6877v'])
specs = device['specs'].replace("'", "")

with open(out_file, 'w') as f:
    for k,v in [('BRAND',brand),('MODEL',model_name),('DEVICE',device_code),('PRODUCT',device_code),
                ('MANUFACTURER',brand),('FINGERPRINT',fp),('HARDWARE',hw),('BOARD',hw),
                ('DISPLAY',f"{build_id}.{build_num}"),('BASEBAND',baseband),('IMEI1',imei1),
                ('IMEI2',imei2),('SERIAL',serial),('ANDROID_ID',android_id),('GAID',gaid),
                ('WIFI_MAC',wifi_mac),('BT_MAC',bt_mac),('DENSITY',str(density)),
                ('ANDROID_VER',android_ver),('SPECS',specs)]:
        f.write(f"{k}='{v}'\n")
