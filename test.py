import requests

def download_image(url, save_path):
        """
        下载图片并保存到本地
        :param url: 图片的完整网址
        :param save_path: 本地保存路径（如：'images/photo.png'）
        """
        try:
            # 发送GET请求
            response = requests.get(url, stream=True) # stream=True支持大文件流式下载[citation:4]
            response.raise_for_status() # 检查请求是否成功（状态码200）[citation:4]

            # 以二进制写入模式保存图片
            with open(save_path, 'wb') as file:
                for chunk in response.iter_content(chunk_size=8192): # 分块写入[citation:4]
                    file.write(chunk)
            print(f"图片已成功保存至：{save_path}")
        except requests.exceptions.RequestException as e:
            print(f"下载失败，错误信息：{e}")

download_image("https://s1.aigei.com/src/img/png/1a/1ae46564878046479cbe73c0f6414754.png?imageMogr2/auto-orient/thumbnail/!950x950r/gravity/Center/crop/950x950/quality/85/%7CimageView2/2/w/950&e=2051020800&token=P7S2Xpzfz11vAkASLTkfHN7Fw-oOZBecqeJaxypL:tJxu727f5foNTioVHBAGbovFVLo=","photo.png")