# Generated by Django 5.0.1 on 2024-01-13 12:40

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0001_initial'),
    ]

    operations = [
        migrations.CreateModel(
            name='Packages',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=250)),
                ('description', models.TextField(blank=True, null=True)),
                ('product_id', models.CharField(max_length=500)),
                ('price_id', models.CharField(max_length=500, null=True)),
                ('amount', models.FloatField(blank=True, null=True)),
                ('currency', models.CharField(default='EUR', max_length=20)),
                ('mode', models.CharField(max_length=250)),
                ('recurring_period', models.CharField(max_length=10)),
                ('features', models.JSONField(blank=True, max_length=500, null=True)),
            ],
        ),
        migrations.AddField(
            model_name='customuser',
            name='stripe_customer_id',
            field=models.CharField(blank=True, max_length=100, null=True),
        ),
        migrations.AddField(
            model_name='customuser',
            name='stripe_customer_response',
            field=models.JSONField(blank=True, max_length=1000, null=True),
        ),
        migrations.CreateModel(
            name='InvoiceDetail',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_file', models.FileField(blank=True, null=True, upload_to='payment/files/invoices/')),
                ('invoice_number', models.CharField(default='0', max_length=500, unique=True)),
                ('plan_start_date', models.DateField(blank=True, null=True)),
                ('plan_end_date', models.DateField(blank=True, null=True)),
                ('invoice_date', models.DateField(blank=True, null=True)),
                ('quantity', models.IntegerField(blank=True, null=True)),
                ('sub_total', models.FloatField(blank=True, null=True)),
                ('total', models.FloatField(blank=True, null=True)),
                ('price_id', models.CharField(blank=True, max_length=500, null=True)),
                ('user_mobile_no', models.CharField(blank=True, max_length=500, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='UserPaymentInfo',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_payment_method_id', models.CharField(blank=True, max_length=100)),
                ('stripe_payment_method_response', models.JSONField(blank=True, max_length=500, null=True)),
                ('ptype', models.CharField(blank=True, max_length=50)),
                ('card_no', models.CharField(blank=True, max_length=20)),
                ('exp_month', models.CharField(blank=True, max_length=10)),
                ('exp_year', models.CharField(blank=True, max_length=10)),
                ('cvv_no', models.CharField(blank=True, max_length=10)),
                ('billing_address', models.TextField(blank=True, max_length=1000, null=True)),
                ('currency', models.CharField(blank=True, max_length=25)),
                ('is_default', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='PaymentHistory',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('invoice_download_link', models.CharField(blank=True, max_length=600, null=True)),
                ('payment_type', models.CharField(blank=True, max_length=100, null=True)),
                ('currency', models.CharField(blank=True, max_length=300, null=True)),
                ('payment_id', models.CharField(blank=True, max_length=100, null=True)),
                ('payment_response', models.JSONField(blank=True, max_length=2000, null=True)),
                ('amount', models.FloatField(blank=True, null=True)),
                ('description', models.CharField(blank=True, max_length=200, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app.invoicedetail')),
                ('package', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app.packages')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to=settings.AUTH_USER_MODEL)),
                ('payment_method', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, to='app.userpaymentinfo')),
            ],
        ),
        migrations.CreateModel(
            name='UserSubscription',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('subscription_plan', models.CharField(blank=True, max_length=250, null=True)),
                ('stripe_customer_id', models.CharField(blank=True, max_length=100)),
                ('stripe_subscription_id', models.CharField(blank=True, max_length=100)),
                ('stripe_subscription_response', models.JSONField(blank=True, max_length=500, null=True)),
                ('status', models.CharField(blank=True, default='active', max_length=100)),
                ('quota', models.JSONField(blank=True, max_length=500, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True, null=True)),
                ('updated_at', models.DateTimeField(auto_now=True, null=True)),
                ('package', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.packages')),
                ('user', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
