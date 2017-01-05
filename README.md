# crest

Cisco APIC-EMのREST APIを利用するPythonスクリプトの例です。

Pythonは3を想定しています。


## 使い方

APIC-EMのアドレス、ユーザ名、パスワード、（場合によってはプロキシサーバ）が必要です。
crest/lib/apicem/config.pyを書き換えてください。

## スクリプトの実行

crest/scriptsにサンプルスクリプトを置いています。

### aem-get.py

aem-get.pyの引数にAPIのURLを与えると、レスポンスをダンプします。

```
C:\HOME\iida\git\crest\scripts>aem-get.py /host
{
  "data": {
    "response": [
      {
        "connectedAPName": "AP7081.059f.19ca",
        "pointOfAttachment": "ae19cd21-1b26-4f58-8ccd-d265deabb6c3",
        "hostType": "wireless",
        "connectedNetworkDeviceId": "cd6d9b24-839b-4d58-adfe-3fdf781e1782",
        "subType": "UNKNOWN",
        "id": "48cdeb9b-b412-491e-a80c-7ec5bbe98167",
        "source": "200",
        "connectedNetworkDeviceIpAddress": "10.1.14.3",
        "connectedAPMacAddress": "68:bc:0c:63:4a:b0",
        "lastUpdated": "1479514114932",
        "hostIp": "10.1.15.117",
        "hostMac": "00:24:d7:43:59:d8",
        "vlanId": "600",
        "pointOfPresence": "ae19cd21-1b26-4f58-8ccd-d265deabb6c3"
      },
      {
        "id": "f624d4f3-0ab9-4ae3-b09d-62051edbd8f3",
        "hostType": "wired",
        "connectedNetworkDeviceId": "26450a30-57d8-4b56-b8f1-6fc535d67645",
        "connectedInterfaceId": "7075521d-4d7b-4218-92f9-79b60e054635",
        "connectedNetworkDeviceIpAddress": "10.2.1.17",
        "source": "200",
        "lastUpdated": "1479514299803",
        "connectedInterfaceName": "GigabitEthernet1/0/47",
        "hostIp": "10.2.1.22",
        "hostMac": "5c:f9:dd:52:07:78",
        "vlanId": "200",
        "subType": "UNKNOWN"
      }
    ],
    "version": "1.0"
  },
  "status_code": 200,
  "Content-Type": "application/json;charset=UTF-8"
}
```


### aem-get-host.py

/hostにGETした結果を整形して表示します。

```
C:\HOME\iida\git\crest\scripts>aem-get-host.py
===========  ========  =============================
host IP      type      connected to network device
===========  ========  =============================
10.1.15.117  wireless  10.1.14.3
10.2.1.22    wired     10.2.1.17
10.1.12.20   wired     10.1.12.1
===========  ========  =============================
```

### aem-get-network-device.py

/network-deviceにGETした結果を整形して表示します。

```
C:\HOME\iida\git\crest\scripts>aem-get-network-device.py
=============================  =============  ==============================================  ====================================
..                             hostname       ip              type
=============================  =============  ==============================================  ====================================
AHEC-2960C1                    165.10.1.39    Cisco Catalyst 2960C-8PC-L Switch               8dbd8068-1091-4cde-8cf5-d1b58dc5c9c7
AP7081.059f.19ca               10.1.14.3      Cisco 3500I Unified Access Point                cd6d9b24-839b-4d58-adfe-3fdf781e1782
Branch-Access1                 10.2.1.17      Cisco Catalyst 29xx Stack-able Ethernet Switch  26450a30-57d8-4b56-b8f1-6fc535d67645
Branch-Router1                 10.2.2.1       Cisco 2911 Integrated Services Router G2        0dd240fd-5cca-4774-a801-9f1c04edcc70
Branch-Router2                 10.2.2.2       Cisco 2911 Integrated Services Router G2        6ce631db-9212-4587-867f-b8f3aed1702d
Branch2-Router.yourdomain.com  218.1.100.100  Cisco 2911 Integrated Services Router G2        d337811b-d371-444c-a49f-9e2791f955b4
CAMPUS-Access1                 10.1.12.1      Cisco Catalyst 3850-48U-E Switch                5b5ea8da-8c23-486a-b95e-7429684d25fc
CAMPUS-Core1                   10.1.7.1       Cisco Catalyst 6503 Switch                      30d39b18-9ada-4148-ad6c-2ee20975b845
CAMPUS-Core2                   10.1.10.1      Cisco Catalyst 6503 Switch                      1b329f52-95eb-44ad-9314-55932162ab86
CAMPUS-Dist1                   10.255.1.5     Cisco Catalyst 4507R plus E Switch              c8ed3e49-5eeb-4dee-b120-edeb179c8394
CAMPUS-Dist2                   10.1.11.1      Cisco Catalyst 4507R plus E Switch              4af8bf34-295f-46f4-97b7-0a2d2ea4cf22
CAMPUS-Router1                 10.1.2.1       Cisco 4451 Series Integrated Services Router    9712ab62-6140-43fd-b1ee-1b07d1fb67d7
CAMPUS-Router2                 10.1.4.2       Cisco 4451 Series Integrated Services Router    55450140-de19-47b5-ae80-bfd741b23fd9
Campus-WLC-5508                10.1.14.2      Cisco 5508 Wireless LAN Controller              ae19cd21-1b26-4f58-8ccd-d265deabb6c3
=============================  =============  ==============================================  ====================================
```

### aem-get-network-device-iplist.py

/network-device-iplistにGETした結果を整形して表示します。

```
C:\HOME\iida\git\crest\scripts>aem-get-network-device-iplist.py
========  ==============  =============
  number  type            ip
========  ==============  =============
       1  host            10.1.15.117
       2  host            10.2.1.22
       3  host            10.1.12.20
       4  network device  165.10.1.39
       5  network device  10.1.14.3
       6  network device  10.2.1.17
       7  network device  10.2.2.1
       8  network device  10.2.2.2
       9  network device  218.1.100.100
      10  network device  10.1.12.1
      11  network device  10.1.7.1
      12  network device  10.1.10.1
      13  network device  10.255.1.5
      14  network device  10.1.11.1
      15  network device  10.1.2.1
      16  network device  10.1.4.2
      17  network device  10.1.14.2
========  ==============  =============
```

### aem-get-network-device-config.py

実行してみてください。


### aem-get-interface.py

実行してみてください。
