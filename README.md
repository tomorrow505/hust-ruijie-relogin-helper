# hust-ruijie-relogin-helper
华科锐捷认证重连工具-基于网页认证。（2023.09.10）

### 前言

----

最近的第二次更新，因为学校最近实行某种策略，3点左右断网，然后最近给别人配的时候不熟练的话不是很方便，所以索性再更新一次，以前的直接删掉了，最后有封装好的桌面程序，可以跳过代码分析直接下载。程序设置为开机自启动，一分钟检验一次。<br>

**New-> 2023.09.09看到有人反馈失效了，提示密码要加密，所以连忙又搞了一个加密版本。**

### 更新后的思路

之前是F12直接抓请求拿加密的密码和querystring，现在把这个过程也给剖开了，因为最近F12不太好拿，所以使用了Fiddler工具，这是个抓包的软件，配置过程就不说了。我们断网看看请求过程：

1. 首先断网打开网页看看会跳转一个认证网页：我这里是http://192.168.50.3:8080/ ，无线和有线还不太一样，但是问题不大。

[![a1.png](https://www.z4a.net/images/2022/04/02/a1.png)](https://www.z4a.net/image/2HWPDN)

2. 打开fiddler访问192.168.50.3:8080，看请求：

[![a2.png](https://www.z4a.net/images/2022/04/02/a2.png)](https://www.z4a.net/image/2HWM4w)

![image](https://github.com/tomorrow505/hust-ruijie-relogin-helper/assets/32202634/30eb3c1a-db31-49fb-b87b-a1b7fc4af2d1)

[![a4.png](https://www.z4a.net/images/2022/04/03/a4.png)](https://www.z4a.net/image/2HuvyJ)

我们发现第一个图的前两个请求都是302，然后会有一个200的请求到123.123.123.123，然后第5个请求就是我们之前页面跳转之后登陆页面网址。然后第二个图进入到一个method=login的请求，这肯定就是我们需要模拟的登录请求了。

[![a5.png](https://www.z4a.net/images/2022/04/03/a5.png)](https://www.z4a.net/image/2HuGGK)

[![a6.png](https://www.z4a.net/images/2022/04/03/a6.png)](https://www.z4a.net/image/2HufKr)

从webform我们可以知道提交了我们的学号，然后密码变成了一串不认识的东西，还有一些空的字段。然后querystring是不是很眼熟，其实就是登陆页面网址的后半部分，这个根据最后的经验是一个跟本机mac地址等相关的一个字符串，具体怎么生成的暂时不追究了，猜想是请求123.123.123.123的时候根据请求头自动生成的。以及最后一个passwordEncrypt，默认为true。也就是说默认是加密的了现在，之前改成false就可以直接使用密码登录，现在需要加密一下，我们需要探索一下加密过程：

![image](https://github.com/tomorrow505/hust-ruijie-relogin-helper/assets/32202634/80b44ad2-2d0c-4a17-a8e3-0a3f2bc4b8d9)

点开源代码的js文件看到了这么几行，然后是调用的security.js，那么使用python模拟这几行的过程就可以了，大致为使用RSA进行加密，其中有两个重要参数publicKeyExponent和publicKeyModulus。

这两个在登录页面上是可以看到的，但是如何通过请求来获取呢？图2有一个pageinfo请求就可以得到了~提交的也就是querystring。

![image](https://github.com/tomorrow505/hust-ruijie-relogin-helper/assets/32202634/bf559b77-e8fd-4a0e-b5e4-ce95241f4aef)


接下来就是要探索querystring怎么用代码获取，仔细查看点开看图1第3个请求：看到返回的数据大致就明白了，跟我们猜想的基本一致。有线和无线可能网址还不一样，无线好像是178开头的，所以我们需要从上述请求返回值得到两个东西：192.168.50.3和wlanuserip开头到结束的部分。

[![a3.png](https://www.z4a.net/images/2022/04/02/a3.png)](https://www.z4a.net/image/2HWIOC)

3. 看代码——获取querystring：请求头与上述一致，由于如果网络没问题就会请求不到querystring，所以自己抛出一个异常，避免程序崩溃。

```python
class internetWorkingFine(Exception):
    def __init__(self, ErrorInfo):
        super().__init__(self)
        self.ErrorInfo=ErrorInfo
    def __str__(self):
        return self.ErrorInfo

def get_info():
    redirect_host = 'http://123.123.123.123/'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,tr;q=0.8,en-US;q=0.7,en;q=0.6",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/98.0.4758.102 Safari/537.36",
        "Upgrade-Insecure-Requests": "1",
        "Host": "123.123.123.123",
        "Proxy-Connection": "keep-alive"
    }
    info = {}
    res = requests.get(redirect_host, headers=headers).content.decode()
    # 这部分根据提交数据观察需要urlencode一下，=和&符号要替换
    info["querystr"] = res[(res.find("wlanuserip")):(res.find("'</script>"))].replace('=','%3D').replace('&','%26')
    if not info["querystr"]:
        raise internetWorkingFine("网络似乎正常~~")
    info["url"] = res[res.find('http:'):res.find('eportal')]
    return info
```

4. 那么接下来的流程就比较清晰了，就需要判断是不是有网，没网就从123.123.123.123获取一下自己的querystring，然后提交data。首先是判断是否掉网：

```python
def get_response():
    try:
        requests.get("https://www.baidu.com")
    except Exception as exc:
        print("当前网络状态出现问题~~")
        relogin()

def get_password(pwd, exponent, modulus):
    e = int(exponent, 16)
    m = int(modulus, 16)
    # 16进制转10进制
    t = pwd.encode('utf-8')
    # 字符串逆向并转换为bytes
    input_nr = int.from_bytes(t, byteorder='big')
    # 将字节转化成int型数字，如果没有标明进制，看做ascii码值
    crypt_nr = pow(input_nr, e, m)
    # 计算x的y次方，如果z在存在，则再对结果进行取模，其结果等效于pow(x,y) %z
    length = ceil(m.bit_length() / 8)
    # 取模数的比特长度(二进制长度)，除以8将比特转为字节
    crypt_data = crypt_nr.to_bytes(length, byteorder='big')
    # 将密文转换为bytes存储(8字节)，返回hex(16字节)
    return crypt_data.hex()

        
def relogin(uid, pwd):
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/96.0.4664.45 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "charset": "UTF-8",
    }
    session = requests.session()
    pageinfo_url = "{url}eportal/InterFace.do?method=pageInfo".format(url=info["url"])
    page_data = {
        "queryString": info["querystr"]
    }
    req = session.post(pageinfo_url, headers=headers, data=page_data).json()
    exponent = req["publicKeyExponent"]
    modulus = req["publicKeyModulus"]
    password = get_password(pwd, exponent, modulus)

    login_url = "{url}eportal/InterFace.do?method=login".format(url=info["url"])

    login_data = {
        "userId": str(uid),
        "password": password,
        "service": "",
        "queryString": info["querystr"],
        "operatorPwd": "",
        "operatorUserId": "",
        "validcode": "",
        "passwordEncrypt": "true"
    }
    req = session.post(url=login_url, headers=headers, data=login_data).json()
    if req["result"] == "fail":
        return "重新认证失败：" + req["message"]
    return "重新认证成功~~~"
```

先是获取querystring，然后通过pageInfo获取加密的指数和模块，接着是在网上找到的不填充版本的加密代码获取加密后的密码（使用浏览器页面的js代码做验证），最后提交认证。

### 打包

---

基本上源代码已经差不多了，整理一下就可以了，为了方便使用，这里重新封装好了一个可以用的exe程序，仍然发布到蝴蝶，使用方式就是在yml文件里指定id和密码，然后一分钟运行一次，方便的话可以设置为开机启动。

```yaml
info:
  userId: M202177777 # 学号
  password: mima123  # 密码
```


运行途中如果出现掉网会记录log：

```javascript
09/10/2023 12:10:39 PM - Error: 当前网络状态出现问题~~
09/10/2023 12:10:39 PM - Relogin 重新认证成功~~~
09/10/2023 12:12:58 PM - Error: 当前网络状态出现问题~~
09/10/2023 12:12:58 PM - Relogin 重新认证成功~~~
```


上述result显示success即可。

### 总结

----

折腾不易，且行且珍惜。
