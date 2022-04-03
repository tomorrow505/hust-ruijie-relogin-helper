# hust-ruijie-relogin-helper
华科锐捷认证重连工具-基于网页认证。

### 前言

----

最近的第二次更新，因为学校最近实行某种策略，3点左右断网，然后最近给别人配的时候不熟练的话不是很方便，所以索性再更新一次，以前的直接删掉了，最后有封装好的桌面程序，可以跳过代码分析直接下载。程序设置为开机自启动，一分钟检验一次。

### 思路

之前是F12直接抓请求拿加密的密码和querystring，现在把这个过程也给剖开了，因为最近F12不太好拿，所以使用了Fiddler工具，这是个抓包的软件，配置过程就不说了。我们断网看看请求过程：

1. 首先断网打开网页看看会跳转一个认证网页：我这里是http://192.168.50.3:8080/，无线和有线还不太一样，但是问题不大。

[![a1.png](https://www.z4a.net/images/2022/04/02/a1.png)](https://www.z4a.net/image/2HWPDN)

2. 访问192.168.50.3，打开fiddler看请求：

[![a2.png](https://www.z4a.net/images/2022/04/02/a2.png)](https://www.z4a.net/image/2HWM4w)

[![a4.png](https://www.z4a.net/images/2022/04/03/a4.png)](https://www.z4a.net/image/2HuvyJ)

我们发现第一个图的前两个请求都是302，然后会有一个200的请求到123.123.123.123，然后第5个请求就是我们之前页面跳转之后登陆页面网址。然后第二个图进入到一个method=login的请求，这肯定就是我们需要模拟的登录请求了。

[![a5.png](https://www.z4a.net/images/2022/04/03/a5.png)](https://www.z4a.net/image/2HuGGK)

[![a6.png](https://www.z4a.net/images/2022/04/03/a6.png)](https://www.z4a.net/image/2HufKr)

从webform我们可以知道提交了我们的学号，然后密码变成了一串不认识的东西，还有一些空的字段。然后querystring是不是很眼熟，其实就是登陆页面网址的后半部分，这个根据最后的经验是一个跟本机mac地址等相关的一个字符串，具体怎么生成的暂时不追究了，猜想是请求123.123.123.123的时候根据请求头自动生成的。以及最后一个passwordEncrypt，默认为true。我们知道一个form提交一般都会有对应name的input框，所以进入F12查看元素：

[![a7.png](https://www.z4a.net/images/2022/04/03/a7.png)](https://www.z4a.net/image/2HuDnj)

发现这个东西是hidden的，也就是页面不会展示的，于是乎退出网络将它改成false再度登录查看表单数据：

[![a8.png](https://www.z4a.net/images/2022/04/03/a8.png)](https://www.z4a.net/image/2Hu3hO)

此时的密码已经变成明文的了，也就是说我们只要获取querystring基本就ok了。

仔细查看点开看图1第3个请求：看到返回的数据大致就明白了，跟我们猜想的基本一致。有线和无线可能网址还不一样，无线好像是178开头的，所以我们需要从上述请求返回值得到两个东西：192.168.50.3和wlanuserip开头到结束的部分。

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

        
def relogin(uid, pwd):
    info = get_info()
    url = "{url}eportal/InterFace.do?method=login".format(url=info["url"])
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.45 Safari/537.36",
        "Content-Type": "application/x-www-form-urlencoded",
        "charset": "UTF-8",
    }
    data = "userId="+str(uid)+"&password="+str(pwd)+"&service=&queryString=" + \
        info["querystr"] + "&operatorPwd=&operatorUserId=&validcode=&passwordEncrypt=false"

    session = requests.session()
    req = session.post(url=url, headers=headers, data=data).json()
    if req["result"] == "fail":
        return "重新认证失败：" + req["message"]
    return "重新认证成功~~~"
```

由于我们在headers那里指定了Content-Type为application/x-www-form-urlencoded，所以data直接是urlencode形式拼接，也可以指定为json然后提交字典。然后需要提供的就是用户的id和密码。

### 打包

---

基本上源代码已经差不多了，整理一下就可以了，为了方便使用，这里封装好了一个可以用的exe程序，发布到蝴蝶了，使用方式就是在yml文件里指定id和密码，然后一分钟运行一次，方便的话可以设置为开机启动。

```yaml
info:
  userId: M202177777 # 学号
  password: mima123  # 密码
```


运行途中如果出现掉网会记录log：

```javascript
11/29/2021 19:16:40 PM - INFO - get_response - 2021-11-29 19:16:40
11/29/2021 19:16:40 PM - INFO - get_response - Error occurred HTTPSConnectionPool(host='www.baidu.com', port=443): Max retries exceeded with url: / (Caused by SSLError(SSLError(1, '[SSL: CERTIFICATE_VERIFY_FAILED] certificate verify failed (_ssl.c:777)'),))
11/29/2021 19:16:40 PM - INFO - get_response - Relogin {"userIndex":"xxxxxxxxxxxxxxxxxxxxxxxxxxxxx","result":"success","message":"","forwordurl":null,"keepaliveInterval":0,"validCodeUrl":""}
```


上述result显示success即可。

下载地址：https://cloud.tomorrow505.xyz/index.php/s/DTFYgSgWmpnDibF

为了备份：https://github.com/tomorrow505/hust-ruijie-relogin-helper

### 总结

----

折腾不易，且行且珍惜。
