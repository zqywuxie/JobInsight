# Boss招聘网岗位可视化

## 项目介绍

------

本项目旨在利用网络爬虫技术和数据可视化手段，对招聘网站（例如Boss直聘）上的岗位信息进行分析。当前阶段的分析主要集中在薪资水平，后续将逐步扩展到其他方面的分析，如岗位需求、工作地点分布、公司规模等。

## 项目背景

------

随着就业市场的竞争日益激烈，大学生在选择实习公司时常常面临信息不对称和选择困难的问题。很多大学生缺乏对公司及岗位的深入了解，导致在求职过程中容易迷茫和盲目。本项目通过对招聘网站上大量岗位信息的收集和分析，为大学生提供一个客观、数据驱动的选择标准，帮助他们更好地了解市场行情，从而做出更明智的职业选择。通过对薪资水平的分析，可以让大学生了解不同公司、不同岗位的薪资差异，为他们提供参考依据。未来，项目还将进一步分析岗位需求、工作地点分布、公司规模等信息，为求职者提供更全面的就业指导。

## 快速上手

------

- 控制台输入指令下载库

~~~shell
pip install -r requirements.txt
~~~

- 修改数据库信息

~~~py
engine = create_engine('mysql+pymysql://root:密码.@localhost:3306/数据库表?charset=utf8mb4')
~~~

***注：***

***1. 本项目无sql文件，会根据类自动创建数据表***

***2. 本项目原本采用csv文件，对于城市名获取对应的城市ID，但是Boss官网对于城市ID的使用有些问题(猜想就是为了防止爬虫)；***

***默认地址为成都;如果需要爬取其他地方的信息,自行前往官网***

[Boss官方](https://www.zhipin.com/web/geek/job?query=%E5%89%8D%E7%AB%AF&city=101270100) ***选择一个城市获取URL后面的获得city=xxx，修改location_id***



- 绘图方式

项目使用两种绘图方式，读者可以自行选择

**plot_avg_salary_plus（动态绘图如图1 推荐）**

plot_avg_salary（静态绘图图2）

~~~python
def data_show(position):
    	.....
        plot_avg_salary_plus(avg_salary_page, position)
        # plot_avg_salary(avg_salary_page, position)
~~~

------

可以点击公司名进行跳转boss官网

![image-20240619193556390](https://wuxie-image.oss-cn-chengdu.aliyuncs.com/image-20240619193556390.png)



![image-20240619193619778](https://wuxie-image.oss-cn-chengdu.aliyuncs.com/image-20240619193619778.png)

------



![image-20240619193650697](https://wuxie-image.oss-cn-chengdu.aliyuncs.com/image-20240619193650697.png)