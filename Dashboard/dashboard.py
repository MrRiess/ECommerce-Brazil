import streamlit as st
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime
from matplotlib.ticker import FuncFormatter

# Mengatur gaya visualisasi
sns.set(style="whitegrid")

# Fungsi untuk membuat data harian
def create_daily_orders_df(data, start_date, end_date):
    start_date = pd.to_datetime(start_date)
    end_date = pd.to_datetime(end_date)
    filtered = data[(data['order_purchase_timestamp'] >= start_date) & (data['order_purchase_timestamp'] <= end_date)]
    daily_orders = filtered.groupby('order_purchase_timestamp').agg(
        total_orders=('order_id', 'count'),
        total_sales=('price', 'sum')
    ).reset_index()
    return daily_orders

# Fungsi untuk membuat data RFM
def create_rfm_df(data):
    today = datetime(2018, 9, 3)
    rfm = data.groupby('customer_id').agg(
        recency=('order_purchase_timestamp', lambda x: (today - x.max()).days),
        frequency=('order_id', 'count'),
        monetary=('price', 'sum')
    ).reset_index()
    return rfm

# Fungsi untuk analisis kota dengan pengiriman terlama dan tercepat
def create_city_delivery_analysis(data):
    city_delivery = data.groupby(['seller_city', 'seller_state']).agg(
        avg_delivery_delay=('delivery_delay_days', 'mean'),
        total_orders=('order_id', 'count')
    ).reset_index()
    
    top_5_delayed = city_delivery.nlargest(5, 'avg_delivery_delay')
    top_5_fastest = city_delivery.nsmallest(5, 'avg_delivery_delay')
    
    return top_5_delayed, top_5_fastest

# Fungsi untuk analisis kota yang paling sering terlambat dan tepat waktu
def create_city_lateness_analysis(data):
    city_lateness = data.groupby(['seller_city', 'seller_state']).agg(
        total_late_orders=('delivery_delay_days', lambda x: (x > 0).sum()),  # Jumlah keterlambatan > 0
        total_ontime_orders=('delivery_delay_days', lambda x: (x == 0).sum()),  # Jumlah pengiriman tepat waktu
        total_orders=('order_id', 'count')
    ).reset_index()
    
    most_late = city_lateness.nlargest(5, 'total_late_orders')
    most_ontime = city_lateness.nlargest(5, 'total_ontime_orders')
    
    return most_late, most_ontime

# Fungsi untuk analisis penjualan tiap bulan
def create_monthly_sales(data):
    monthly_sales = data.groupby(['year', 'month']).agg(
        total_sales=('price', 'sum')
    ).reset_index()
    return monthly_sales

# Fungsi untuk analisis tren product_category_name tiap tahun
def create_category_trends(data):
    if 'product_category_name' not in data.columns:
        st.error("Kolom 'product_category_name' tidak ditemukan dalam dataset.")
        return None
    
    category_trends = data.groupby(['year', 'product_category_name']).agg(
        total_sales=('price', 'sum')
    ).reset_index()

    top_10_category_trends = category_trends.groupby('year').apply(
        lambda x: x.nlargest(10, 'total_sales')
    ).reset_index(drop=True)
    
    return top_10_category_trends

# Fungsi untuk analisis top 10 penjualan kategori produk tiap tahun
def create_top_10_sales_per_year(data):
    data['year'] = data['order_purchase_timestamp'].dt.year
    top_10_per_year = data.groupby(['year', 'product_category_name']).agg(
        total_sales=('price', 'sum')
    ).reset_index()
    
    top_10_per_year = top_10_per_year.groupby('year').apply(
        lambda x: x.nlargest(10, 'total_sales')
    ).reset_index(drop=True)
    
    return top_10_per_year

# Fungsi untuk menghitung pertumbuhan penjualan
def calculate_growth(data):
    if 'total_sales' not in data.columns:
        st.error("Kolom 'total_sales' tidak ditemukan dalam dataset.")
        return data
    
    data['previous_month_sales'] = data.groupby('product_category_name')['total_sales'].shift(1)
    data['growth'] = (data['total_sales'] - data['previous_month_sales']) / data['previous_month_sales'] * 100
    return data

# Fungsi utama untuk Streamlit
def main():
    st.title("Dashboard Penjualan dan Analisis Pelanggan")

    # Membaca dataset langsung dari path yang sudah diberikan
# URL dataset
    url = "https://raw.githubusercontent.com/MrRiess/Proyek-Data-Analyst-1/main/Dashboard/product_orders_sellers_review_customer_merged.csv"
    data = pd.read_csv(url, parse_dates=['order_purchase_timestamp', 'order_delivered_customer_date'])

    # Menampilkan data yang diunggah
    st.subheader("Data yang Diunggah")
    st.dataframe(data.head(10))

    # Sidebar filter
    st.sidebar.header("Filter Data")
    start_date = st.sidebar.date_input("Tanggal Mulai", min_value=data['order_purchase_timestamp'].min().date(), value=data['order_purchase_timestamp'].min().date())
    end_date = st.sidebar.date_input("Tanggal Akhir", max_value=data['order_purchase_timestamp'].max().date(), value=data['order_purchase_timestamp'].max().date())

    # Analisis Harian
    st.subheader("Analisis Penjualan Harian")
    daily_orders = create_daily_orders_df(data, start_date, end_date)
    st.write(f"Total Pesanan: {daily_orders['total_orders'].sum()}, Total Pendapatan: ${daily_orders['total_sales'].sum():,.2f}")
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=daily_orders, x='order_purchase_timestamp', y='total_sales', ax=ax, marker='o')
    ax.set_title("Total Penjualan Harian")
    ax.set_xlabel("Tanggal")
    ax.set_ylabel("Total Penjualan (USD)")
    ax.set_ylim(0, 140_000)
    ax.set_yticklabels([f'{int(x/1000)}K' for x in ax.get_yticks()])
    st.pyplot(fig)

    # Penjualan Tiap Bulan
    st.subheader("Penjualan Tiap Bulan")
    monthly_sales = create_monthly_sales(data)
    fig, ax = plt.subplots(figsize=(10, 5))
    sns.lineplot(data=monthly_sales, x='month', y='total_sales', hue='year', marker='o', ax=ax)
    ax.set_title("Penjualan Bulanan")
    ax.set_xlabel("Bulan")
    ax.set_ylabel("Total Penjualan (USD)")
    ax.set_xticks(range(1, 13))
    ax.set_xticklabels(['Jan', 'Feb', 'Mar', 'Apr', 'May', 'Jun', 'Jul', 'Aug', 'Sep', 'Oct', 'Nov', 'Dec'])
    ax.set_ylim(0, 1100_000)
    ax.set_yticklabels([f'{int(x/1000)}K' for x in ax.get_yticks()])
    # Menambahkan label di setiap titik
    for line in ax.lines:
        for x, y in zip(line.get_xdata(), line.get_ydata()):
            ax.annotate(f'{y/1000:.1f}K', (x, y), textcoords="offset points", xytext=(0, 5), ha='center')
    st.pyplot(fig)

    # Tren per Tahun per Kategori Produk (Top 10)
    st.subheader("Tren Penjualan per Tahun per Kategori Produk")
    category_trends = create_category_trends(data)
    if category_trends is not None:
        fig, ax = plt.subplots(figsize=(10, 5))
        sns.lineplot(data=category_trends, x='year', y='total_sales', hue='product_category_name', marker='o', ax=ax)
        ax.set_title("Tren Penjualan per Kategori Produk per Tahun (Top 10)")
        ax.set_xlabel("Tahun")
        ax.set_ylabel("Total Penjualan (USD)")
        ax.set_ylim(0, 900_000)
        ax.set_yticklabels([f'{int(x/1000)}K' for x in ax.get_yticks()])
        ax.set_xticks([2016, 2017, 2018])
        ax.set_xticklabels(['2016', '2017', '2018'])
        for line in ax.lines:
            for x, y in zip(line.get_xdata(), line.get_ydata()):
                if x in [2018]:  # Hanya untuk tahun 2018
                    ax.annotate(f'{y/1000:.2f}K', (x, y), textcoords="offset points", xytext=(0, 5), ha='center')
    st.pyplot(fig)
    
    # Top 10 Penjualan Kategori Produk per Tahun
    st.subheader("Top 10 Penjualan Kategori Produk per Tahun")
    top_10_sales_per_year = create_top_10_sales_per_year(data)
    fig, axes = plt.subplots(3, 1, figsize=(14, 18))
    years = [2016, 2017, 2018]

    for i, year in enumerate(years):
        top_10 = top_10_sales_per_year[top_10_sales_per_year['year'] == year]
        sns.barplot(data=top_10, x='total_sales', y='product_category_name', ax=axes[i], palette="viridis")
        axes[i].set_title(f"Top 10 Penjualan Kategori Produk pada Tahun {year}")
        axes[i].set_xlabel("Total Penjualan (USD)")
        axes[i].set_ylabel("Kategori Produk")
        axes[i].set_xticklabels([f'{int(x/1000)}K' for x in axes[i].get_xticks()])
        axes[i].set_xlim(0, top_10['total_sales'].max()*1.1)
        for container in axes[i].containers:
            labels = [f'{(v/1000):,.2f}K' for v in container.datavalues]
            axes[i].bar_label(container, labels=labels, label_type="edge")
    st.pyplot(fig)
    
    # Produk Terbaik dan Terburuk
    st.subheader("Produk Terbaik dan Terburuk (Total Penjualan 2016 - 2018)")
    product_sales = data.groupby('product_category_name').agg(total_sales=('price', 'sum')).reset_index()
    top_products = product_sales.nlargest(5, 'total_sales')
    bottom_products = product_sales.nsmallest(5, 'total_sales')
    fig, ax = plt.subplots(2, 1, figsize=(14, 12))

        # Top Products - Sales
    sns.barplot(data=top_products, x='total_sales', y='product_category_name', ax=ax[0], palette="viridis")
    ax[0].set_title("Top 5 Produk")
    ax[0].set_xlabel("Total Penjualan (USD)")
    ax[0].set_ylabel("Kategori Produk")
    ax[0].set_xlim(0, 1300_000)
    ax[0].set_xticklabels([f'{int(x/1000)}K' for x in ax[0].get_xticks()])
    for container in ax[0].containers:
        labels = [f'{(v/1000):,.2f}K' for v in container.datavalues]
        ax[0].bar_label(container, labels=labels, label_type="edge")

        # Bottom Products - Sales
    sns.barplot(data=bottom_products, x='total_sales', y='product_category_name', ax=ax[1], palette="viridis")
    ax[1].set_title("Bottom 5 Produk")
    ax[1].set_xlabel("Total Penjualan (USD)")
    ax[1].set_ylabel("Kategori Produk")
    ax[1].set_xlim(0, 1000)
    for i in ax[1].containers:
        ax[1].bar_label(i, label_type="edge")

    st.pyplot(fig)

    # Produk Terbaik dan Terburuk
    st.subheader("Produk Terbaik dan Terburuk (Total Pesanan 2016 - 2018)")
    product_sales = data.groupby('product_category_name').agg(total_orders=('order_id', 'count')).reset_index()
    top_products = product_sales.nlargest(5, 'total_orders')
    bottom_products = product_sales.nsmallest(5, 'total_orders')

    fig, ax = plt.subplots(2, 1, figsize=(14, 12))
    
    # Top Products - Orders
    sns.barplot(data=top_products, x='total_orders', y='product_category_name', ax=ax[0], palette="viridis")
    ax[0].set_title("Top 5 Produk (Total Pesanan)")
    ax[0].set_xlabel("Total Pesanan")
    ax[0].set_ylabel("Kategori Produk")
    ax[0].set_xlim(0, 11_000)
    ax[0].set_xticklabels([f'{int(x/1000)}K' for x in ax[0].get_xticks()])
    for container in ax[0].containers:
        labels = [f'{(v/1000):,.2f}K' for v in container.datavalues]
        ax[0].bar_label(container, labels=labels, label_type="edge")

    # Bottom Products - Orders
    sns.barplot(data=bottom_products, x='total_orders', y='product_category_name', ax=ax[1], palette="viridis")
    ax[1].set_title("Bottom 5 Produk (Total Pesanan)")
    ax[1].set_xlabel("Total Pesanan")
    ax[1].set_ylabel("Kategori Produk")
    ax[1].set_xlim(0, 25)
    for i in ax[1].containers:
        ax[1].bar_label(i, label_type="edge")

    st.pyplot(fig)

    # Analisis RFM
    st.subheader("Analisis Pelanggan Terbaik (RFM)")
    rfm = create_rfm_df(data)
    rfm_summary = rfm.describe()
    st.write("Statistik RFM")
    st.write(rfm_summary)

    top_rfm = rfm.nlargest(5, 'monetary')
    st.write("Top 5 Pelanggan Berdasarkan Pengeluaran")
    st.dataframe(top_rfm)

    # Analisis Pengiriman Kota
    st.subheader("Kota dengan Pengiriman Terlama dan Tercepat")
    top_5_delayed, top_5_fastest = create_city_delivery_analysis(data)
    
    # Kota dengan Pengiriman Terlama
    st.write("Top 5 Kota dengan Pengiriman Terlama")
    st.dataframe(top_5_delayed)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=top_5_delayed, x='avg_delivery_delay', y='seller_city', ax=ax, palette="Reds")
    ax.set_title("Top 5 Kota dengan Pengiriman Terlama")
    ax.set_xlabel("Rata-rata Keterlambatan Pengiriman (Hari)")
    ax.set_ylabel("Kota Penjual")
    for i in ax.containers:
        ax.bar_label(i, label_type="edge")
    st.pyplot(fig)

    # Kota dengan Pengiriman Tercepat
    st.write("Top 5 Kota dengan Pengiriman Tercepat")
    st.dataframe(top_5_fastest)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=top_5_fastest, x='avg_delivery_delay', y='seller_city', ax=ax, palette="Blues")
    ax.set_title("Top 5 Kota dengan Pengiriman Tercepat")
    ax.set_xlabel("Rata-rata Keterlambatan Pengiriman (Hari)")
    ax.set_ylabel("Kota Penjual")
    for i in ax.containers:
        ax.bar_label(i, label_type="edge")
    st.pyplot(fig)

    # Analisis Kota yang Paling Sering Terlambat dan Tepat Waktu
    st.subheader("Kota yang Paling Sering Terlambat dan Tepat Waktu dalam Pengiriman")
    most_late, most_ontime = create_city_lateness_analysis(data)

    # Kota yang Paling Sering Terlambat
    st.write("Top 5 Kota yang Paling Sering Terlambat")
    st.dataframe(most_late)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=most_late, x='total_late_orders', y='seller_city', ax=ax, palette="Reds")
    ax.set_title("Top 5 Kota yang Paling Sering Terlambat")
    ax.set_xlabel("Jumlah Keterlambatan Pengiriman")
    ax.set_ylabel("Kota Penjual")
    ax.set_xlim(0, 25_000)
    ax.set_xticklabels([f'{int(x/1000)}K' for x in ax.get_xticks()])
    for container in ax.containers:
        labels = [f'{(v/1000):,.2f}K' for v in container.datavalues]
        ax.bar_label(container, labels=labels, label_type="edge")
    st.pyplot(fig)

    # Kota yang Tepat Waktu
    st.write("Top 5 Kota yang Tepat Waktu")
    st.dataframe(most_ontime)

    fig, ax = plt.subplots(figsize=(10, 5))
    sns.barplot(data=most_ontime, x='total_ontime_orders', y='seller_city', ax=ax, palette="Greens")
    ax.set_title("Top 5 Kota yang Tepat Waktu")
    ax.set_xlabel("Jumlah Pengiriman Tepat Waktu")
    ax.set_ylabel("Kota Penjual")
    for i in ax.containers:
        ax.bar_label(i, label_type="edge")
    st.pyplot(fig)

if __name__ == "__main__":
    main()
