from DrissionPage import ChromiumPage
from lxml import etree
from time import sleep
from concurrent.futures import ThreadPoolExecutor,as_completed
import csv


def get_goods_url(goods_name):
    # 构造浏览器对象
    driver = ChromiumPage()

    #访问网站
    driver.get("https://www.jd.com/")

    #搜索商品
    driver.ele("css:#key").input(goods_name)

    #点击搜索
    driver.ele("css:.button").click()

    #设置延时
    sleep(2)

    #定义一个空集合
    alists = []
    for i in range(2): #获取前两页数据
        # 将网页数据下滑到最下方
        driver.scroll.to_bottom()
        sleep(3)
        # 数据清洗，将所有的商品路径获取到
        e = etree.HTML(driver.html)
        alist = e.xpath('//*[@id="J_goodsList"]/ul/li/div/div[1]/a/@href')
        for a in alist:
            alists.append("https:"+a)
        driver.ele("css:#J_bottomPage > span.p-num > a.pn-next").click()

    return alists

def get_goods_info(goods_url):
    #因使用到多线程，每个线程操作不同的浏览器对象
    driver_o = ChromiumPage()
    driver_o.get(goods_url)
    sleep(3)
    e = etree.HTML(driver_o.html)

    price = e.xpath('//div[@class="dd"]/span/span[2]')

    if price:
        price = price[0].text
    else:
        price = "未知"
    appraise_number = driver_o.ele("css:#comment-count > a").text
    store_name = driver_o.ele("css:#popbox > div > div.mt > h3 > a").text
    store_url = driver_o.ele("css:#popbox > div > div.mt > h3 > a").attr("href")
    store_url ="https:" + store_url
    goods_introduce = driver_o.eles("css:#detail > div.tab-con > div:nth-child(1) > div.p-parameter > ul.parameter2.p-parameter-list > li")
    goods_introduce = [i.text for i in goods_introduce]
    title = driver_o.ele("css:.sku-name").text.replace('\n', '')

    return {
        "标题": title,
        "价格": price,
        "累积评价": appraise_number,
        "店铺名称": store_name,
        "店铺链接": store_url,
        "商品介绍": goods_introduce
    }

if __name__ == '__main__':
    s = input("请输入你需要查找的商品：")
    print("正在获取数据，请稍候...")
    alists = get_goods_url(s)
    for a in alists:
        print(a)
    print(f"获取到{len(alists)}条商品路径，正在努力抓取数据，请稍候...")
    flag = True

    try:
        with open('./goods.csv', 'a', encoding='utf-8', newline='') as f:
            with ThreadPoolExecutor(max_workers=4) as pool:
                results = [pool.submit(get_goods_info, url) for url in alists]
                for result in as_completed(results):
                    print(f"正在抓取第{results.index(result) + 1}条商品路径中的数据，请稍候...")
                    goods_info = result.result()
                    print(goods_info)
                    print()
                    # 创建一个字典写入器对象
                    writer = csv.DictWriter(f, fieldnames=goods_info.keys())
                    if flag:
                        # 写入表头
                        writer.writeheader()
                        flag = False
                    # 写入数据
                    writer.writerow(goods_info)
    except Exception as e:
        print(f"发生错误：{e}")

