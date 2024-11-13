import os
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'your_secret_key'

# تحديد المسار للملف subscriptions.xlsx في المجلد الفرعي 'data'
file_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'data', '444.xlsx')


# وظيفة لتحميل البيانات من الملف
def load_data():
    return pd.read_excel(file_path)


# دالة لتحديث حالة الاشتراك بناءً على تاريخ الانتهاء
def update_subscription_status(df):
    current_date = datetime.now()
    # تحويل تاريخ الانتهاء في البيانات إلى datetime للتحقق بشكل صحيح
    df['تاريخ الانتهاء'] = pd.to_datetime(df['تاريخ الانتهاء'], errors='coerce')

    def calculate_remaining_time(end_date):
        if pd.isnull(end_date):
            return 'تاريخ غير صحيح'
        delta = end_date - current_date
        if delta.days > 0:
            return f'باقٍ {delta.days} يوم'
        elif delta.days == 0:
            return 'ينتهي اليوم'
        else:
            return f'منتهٍ منذ {-delta.days} يوم'

    # تطبيق دالة حساب الأيام المتبقية على العمود
    df['حالة الاشتراك'] = df['تاريخ الانتهاء'].apply(calculate_remaining_time)
    return df


# الصفحة الرئيسية
@app.route('/')
def home():
    return render_template('index.html')


# عرض الاشتراكات
@app.route('/subscriptions')
def subscriptions():
    df = load_data()
    df = update_subscription_status(df)  # تحديث حالة الاشتراكات
    return render_template('subscriptions.html', subscriptions=df.to_dict(orient='records'))


# عرض الاشتراكات المنتهية
@app.route('/expired_subscriptions')
def expired_subscriptions():
    df = load_data()
    df = update_subscription_status(df)  # تحديث حالة الاشتراكات
    expired_df = df[df['حالة الاشتراك'].str.contains('منتهٍ', case=False)]  # تصفية الاشتراكات المنتهية
    return render_template('expired_subscriptions.html', expired_subscriptions=expired_df.to_dict(orient='records'))


# إضافة اشتراك
@app.route('/add_subscription', methods=['GET', 'POST'])
def add_subscription():
    if request.method == 'POST':
        df = load_data()  # تحميل البيانات في هذه الدالة
        name = request.form['name']
        subscription_date = request.form['subscription_date']
        end_date = request.form['end_date']
        phone = request.form['phone']
        subscription_type = request.form['subscription_type']

        # إضافة بيانات الاشتراك إلى الملف
        new_subscription = {
            'الاســــــم': name,
            'تاريخ الاشتراك': subscription_date,
            'تاريخ الانتهاء': end_date,
            'رقم الهاتف': phone,
            'نوع الاشتراك': subscription_type,
            'حالة الاشتراك': 'باقٍ'  # حالة الاشتراك ستكون "باقٍ" عند الإضافة
        }
        df = pd.concat([df, pd.DataFrame([new_subscription])], ignore_index=True)
        df = update_subscription_status(df)  # تحديث حالة الاشتراك بعد إضافة الاشتراك الجديد
        df.to_excel(file_path, index=False)

        flash("تم إضافة الاشتراك بنجاح!", "success")
        return redirect(url_for('home'))

    return render_template('add_subscription.html')


# حذف اشتراك
@app.route('/delete_subscription', methods=['GET', 'POST'])
def delete_subscription():
    if request.method == 'POST':
        name = request.form['name']
        df = load_data()  # تحميل البيانات في هذه الدالة
        df = update_subscription_status(df)  # تحديث حالة الاشتراكات
        result = df[df['الاســــــم'].str.contains(name, case=False)]

        if not result.empty:
            df.drop(result.index, inplace=True)
            df.to_excel(file_path, index=False)
            flash("تم حذف الاشتراك بنجاح!", "success")
        else:
            flash("الاسم غير موجود في النظام!", "error")
        return redirect(url_for('home'))

    return render_template('delete_subscription.html')


# مسار البحث عن الاشتراك
@app.route('/search_subscription', methods=['GET', 'POST'])
def search_subscription():
    if request.method == 'POST':
        # الحصول على النص المدخل في نموذج البحث
        search_query = request.form.get('search_query')
        df = load_data()  # تحميل البيانات من الملف
        # البحث في العمود المناسب
        result = df[df['الاســــــم'].str.contains(search_query, case=False, na=False)]
        if not result.empty:
            # إذا تم العثور على النتائج
            return render_template('search_subscription.html', search_query=search_query,
                                   subscriptions=result.to_dict(orient='records'))
        else:
            flash("لا توجد اشتراكات تتطابق مع البحث!", "error")
            return render_template('search_subscription.html', search_query=search_query)

    return render_template('search_subscription.html')


if __name__ == '__main__':
    app.run(debug=True)
