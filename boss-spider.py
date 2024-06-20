import asyncio
import re
import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from pyppeteer import launch
import plotly.graph_objects as go
from sqlalchemy import Column, Integer, String
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import plotly.express as px

Base = declarative_base()
MAX_DESCRIPTION_LENGTH = 1024
# 创建数据库连接
engine = create_engine('mysql+pymysql://root:wszqy123.@localhost:3306/boss-work-spider?charset=utf8mb4')


# 建立数据库连接
class Job(Base):
    __tablename__ = 'jobs'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(255))
    area = Column(String(255))
    salary = Column(String(255))
    description = Column(String(1024))
    link = Column(String(1024))
    company = Column(String(255))
    position = Column(String(255))


# 提取最高和最低薪资
def extract_salary(salary):
    if 'K' in salary:
        salary_range = re.findall(r'(\d+)-(\d+)K', salary)
        if salary_range:
            return int(salary_range[0][0]), int(salary_range[0][1])
    elif '元/天' in salary:
        salary_range = re.findall(r'(\d+)-(\d+)', salary)
        if salary_range:
            min_salary = (int(salary_range[0][0]) * 30) / 1000  # 转换为月薪
            max_salary = (int(salary_range[0][1]) * 30) / 1000  # 转换为月薪
            return min_salary, max_salary
    elif '元/月' in salary:
        salary_range = re.findall(r'(\d+)-(\d+)', salary)
        if salary_range:
            return int(salary_range[0][0]) / 1000, int(salary_range[0][1]) / 1000
    return None, None


# 爬虫核心代码
async def start_spider(position, city):
    Base.metadata.create_all(engine)  # 自动创建 jobs 表
    Session = sessionmaker(bind=engine)
    session = Session()
    browser = await launch(executablePath='C:\\Program Files (x86)\\Microsoft\\Edge\\Application\\msedge.exe',
                           headless=False, args=['--no-sandbox'])
    page = await browser.newPage()

    print(city)
    await page.goto(f"https://www.zhipin.com/web/geek/job?query={position}&city={city}")
    await page.waitForSelector('.job-list-box')

    total_page = await page.evaluate('(document.querySelectorAll(".options-pages a:nth-last-child(2)")[0].textContent)')
    total_page = int(total_page)

    all_jobs = []
    for i in range(1, total_page + 1):
        await page.goto(f'https://www.zhipin.com/web/geek/job?query={position}&city={city}&page={i}')
        await page.waitForSelector('.job-list-box')

        jobs = await page.evaluate('''() => {
            const jobs = [];
            const elements = document.querySelectorAll('.job-list-box .job-card-wrapper');
            elements.forEach(item => {
                const job = {
                    name: item.querySelector('.job-name').textContent.trim(),
                    area: item.querySelector('.job-area').textContent.trim(),
                    salary: item.querySelector('.salary').textContent.trim(),
                    link: item.querySelector('a').href,
                    company: item.querySelector('.company-name').textContent.trim()
                };
                jobs.push(job);
            });
            return jobs;
        }''')
        all_jobs.extend(jobs)

    for job in all_jobs:
        await page.goto(job['link'])
        try:
            await page.waitForSelector('.job-sec-text')
            job_desc = await page.evaluate('(document.querySelector(".job-sec-text").textContent)')
            job['description'] = job_desc.strip()[:MAX_DESCRIPTION_LENGTH]  # 截断描述
            new_job = Job(
                name=job['name'],
                area=job['area'],
                salary=job['salary'],
                description=job['description'],
                link=job['link'],
                company=job['company'],
                position=position
            )
            session.add(new_job)
            session.commit()
            print(job)
        except Exception as e:
            print(f'Error: {str(e)}')

    await browser.close()
    data_show(position)
    session.close()


def plot_avg_salary_plus(avg_salary_by_company, position):
    # 添加自定义数据，用于悬停时显示更多信息
    avg_salary_by_company['text'] = avg_salary_by_company.apply(
        lambda row: f"<b>公司:</b> {row['company']}<br>"
                    f"<b>公司地址:</b> {row['area']}<br>"
                    f"<b>最低薪资:</b> {row['min_salary']}K<br>"
                    f"<b>最高薪资:</b> {row['max_salary']}K",
        axis=1
    )

    fig = go.Figure()

    # 调整索引，使得每个数据点之间有一定间隔
    avg_salary_by_company['index'] = avg_salary_by_company.index * 2

    # 绘制最低薪资折线
    fig.add_trace(go.Scatter(x=avg_salary_by_company['index'], y=avg_salary_by_company['min_salary'],
                             mode='lines+markers', name='最低薪资',
                             line=dict(color='blue', width=2),
                             marker=dict(color='blue', size=8),
                             text=avg_salary_by_company['text'],
                             hoverinfo='text'))

    # 绘制最高薪资折线
    fig.add_trace(go.Scatter(x=avg_salary_by_company['index'], y=avg_salary_by_company['max_salary'],
                             mode='lines+markers', name='最高薪资',
                             line=dict(color='red', width=2),
                             marker=dict(color='red', size=8),
                             text=avg_salary_by_company['text'],
                             hoverinfo='text'))

    # 自定义 x 轴标签
    x_labels = []
    for company, link in zip(avg_salary_by_company['company'], avg_salary_by_company['link']):
        label = f"<a href='{link}' target='_blank'>{company}</a>"
        x_labels.append(label)

    # 设置 x 轴标签和超链接，增加展示间隔
    tickvals = avg_salary_by_company['index']
    fig.update_xaxes(type='category', tickmode='array', tickvals=tickvals, ticktext=x_labels)

    # 计算薪资区间百分比
    min_salaries = avg_salary_by_company['min_salary']

    total_entries = len(avg_salary_by_company)
    salary_ranges = [
        (0, 3),
        (3, 5),
        (5, 8),
        (8, 10),
        (10, 15),
        (15, 20),
        (20,float('inf'))
    ]

    salary_percentage_text = ""
    for i, (low, high) in enumerate(salary_ranges):
        range_count = len(min_salaries[(min_salaries >= low) & (min_salaries < high)])
        range_percentage = range_count / total_entries * 100
        salary_percentage_text += f"{low}-{high}K: {range_percentage:.1f}%<br>"

    # 在图表左上角添加薪资区间百分比文本
    fig.add_annotation(
        text=salary_percentage_text,
        xref="paper", yref="paper",
        x=0.01, y=0.99,
        showarrow=False,
        font=dict(size=12, color="black"),
        align="left",
        bordercolor="black", borderwidth=1
    )

    fig.update_layout(
        title={
            'text': f"{position}岗位薪资分析",
            'y': 0.95,
            'x': 0.5,
            'xanchor': 'center',
            'yanchor': 'top',
            'font': {
                'size': 20,
                'color': 'black'
            }
        },
        template='plotly',  # 使用默认模板
    )

    fig.show()


def plot_avg_salary(avg_salary_by_company, position):
    # 按每页20个公司进行分页显示
    num_pages = (len(avg_salary_by_company) - 1) // 20 + 1
    for page in range(num_pages):
        start_idx = page * 20
        end_idx = min((page + 1) * 20, len(avg_salary_by_company))
        avg_salary_page = avg_salary_by_company.iloc[start_idx:end_idx]

        print(avg_salary_page)
        # 绘制交互式图表
        sns.set(style="whitegrid")

        # 设置中文字体
        plt.rcParams['font.sans-serif'] = ['Microsoft YaHei']  # 指定默认字体
        plt.rcParams['axes.unicode_minus'] = False  # 解决保存图像是负号'-'显示为方块的问题

        plt.figure(figsize=(14, 8))
        plt.plot(avg_salary_page['company'], avg_salary_page['min_salary'], marker='o', label='最低工资')
        plt.plot(avg_salary_page['company'], avg_salary_page['max_salary'], marker='o', label='最高工资')

        # 在每个数据点上显示具体数值
        for i, row in avg_salary_page.iterrows():
            plt.annotate(f"{row['min_salary']:.1f}", (row['company'], row['min_salary']), textcoords="offset points",
                         xytext=(0, 5), ha='center')
            plt.annotate(f"{row['max_salary']:.1f}", (row['company'], row['max_salary']), textcoords="offset points",
                         xytext=(0, 5), ha='center')

        # 显示职位名称和分页信息
        plt.title(f'不同公司{position}职位的平均薪资', fontsize=16)
        plt.xlabel('公司', fontsize=14)
        plt.ylabel('薪资 (K)', fontsize=14)
        plt.xticks(rotation=90, fontsize=12)
        plt.yticks(fontsize=12)
        plt.legend(fontsize=12)
        plt.tight_layout()

        plt.show()


# 数据展示函数
def data_show(position):
    # 查询数据
    query = f"SELECT name, area, salary, description, link, company FROM jobs WHERE position = '{position}'"
    df = pd.read_sql(query, engine)
    df[['min_salary', 'max_salary']] = df['salary'].apply(lambda x: pd.Series(extract_salary(x)))
    df.dropna(subset=['min_salary', 'max_salary'], inplace=True)

    # 可视化不同公司的平均薪资
    # 根据公司的平均最低薪资进行排序
    avg_salary_by_company = df.groupby('company').agg({
        'min_salary': 'mean',
        'max_salary': 'mean',
        'link': 'first',  # 选择 link 列的第一个值
        'area': 'first'  # 选择 link 列的第一个值
    }).reset_index()
    # 根据平均最低薪资进行排序
    avg_salary_by_company = avg_salary_by_company.sort_values(by='min_salary')

    plot_avg_salary_plus(avg_salary_by_company, position)


"""
注:从excel读取cityId(boss官网有问题)
"""


def get_location_id_from_csv(file_path, city_name_zh):
    try:
        df = pd.read_csv(file_path, encoding='gbk')
        city_name_zh = city_name_zh.strip()  # 去除城市名首尾空格
        result = df[df['Location_Name_ZH'] == city_name_zh]
        if not result.empty:
            incremented_id = int(result.iloc[0]['Location_ID']) + 1
            return str(incremented_id)
        else:
            return None
    except Exception as e:
        print(f"Error reading CSV file: {str(e)}")
        return None


if __name__ == '__main__':
    position = input("请输入要查询的职位关键词（例如：前端）: ").strip()
    # """
    # # # city = input("请输入要查询的城市(例如: 成都) : ").strip()
    # # # location_id = get_location_id_from_csv("China-City-List-latest.csv", city)
    # # # https://www.zhipin.com/web/geek/job?query=%E5%89%8D%E7%AB%AF&city=101270100
    # # # 因为boss官网的cityId对不上号,默认地址为成都;如果需要爬取其他地方的信息,自行前往上方官方 获得city=xxx
    # """
    location_id = "101270100"  # 成都
    # #  print(location_id)
    asyncio.get_event_loop().run_until_complete(start_spider(position, location_id))
    #
    # # 绘制图表
    data_show(position)
    # data_show("Java实习")
