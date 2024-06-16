import sched
import time
from datetime import datetime
from math import ceil
import requests
import logging
from logging.handlers import RotatingFileHandler
from yaml import load
try:
    from yaml import CLoader as Loader
except ImportError:
    from yaml import Loader


job = sched.scheduler(time.time, time.sleep)


class InternetWorkingFine(Exception):
    def __init__(self, error_info):
        super().__init__(self)  # 初始化父类
        self.error_info = error_info

    def __str__(self):
        return self.error_info


def get_logger():
    instance_log_file = './log.log'
    logging_datefmt = "%m/%d/%Y %H:%M:%S %p"
    logging_format = "%(asctime)s - %(message)s"
    logFormatter = logging.Formatter(fmt=logging_format, datefmt=logging_datefmt)
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    while logger.handlers:
        logger.handlers.pop()
    if instance_log_file:
        fileHandler = RotatingFileHandler(filename=instance_log_file, mode='a', maxBytes=3 * 1024 * 1024,
                                          backupCount=2)
        fileHandler.setFormatter(logFormatter)
        logger.addHandler(fileHandler)
    consoleHandler = logging.StreamHandler()
    consoleHandler.setFormatter(logFormatter)
    logger.addHandler(consoleHandler)
    return logger


def get_response(uid, pwd):
    try:
        requests.get("https://www.baidu.com")
        print("网络似乎正常~~")
    except Exception:
        logger.info("Error: 当前网络状态出现问题~~")
        try:
            relogin_info = relogin(uid, pwd)
            logger.info("Relogin " + relogin_info)
        except Exception as exc:
            logger.info("Relogin trouble occurred: %s " % exc)
    job.enter(60, 0, get_response, (uid, pwd))


def read_data():
    data = load(open('./info.yml', 'rb'), Loader=Loader)
    return data['info']


def get_info():
    redirect_host = 'http://123.123.123.123/'
    headers = {
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,"
                  "application/signed-exchange;v=b3;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "Accept-Language": "zh-CN,zh;q=0.9,tr;q=0.8,en-US;q=0.7,en;q=0.6",
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) "
                      "Chrome/98.0.4758.102 Safari/537.36",
        "Upgrade-Insecure-Requests": "1",
        "Host": "123.123.123.123",
        "Proxy-Connection": "keep-alive"
    }
    info = {}
    res = requests.get(redirect_host, headers=headers).content.decode()
    info["querystr"] = res[(res.find('wlanuserip')):(res.find('\'</script>'))].replace('=', '%3D').replace('&', '%26')
    if not info["querystr"]:
        raise InternetWorkingFine("网络似乎正常~~")
    info["url"] = res[res.find('http:'):res.find('eportal')]
    return info


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
    info = get_info()
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


def monitor(uid, pwd):
    job.enter(0, 0, get_response, (uid, pwd))
    job.run()


if __name__ == '__main__':
    logger = get_logger()
    login_info = read_data()
    monitor(login_info['userId'], login_info['password'])
