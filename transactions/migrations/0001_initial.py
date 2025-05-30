# Generated by Django 5.1.1 on 2024-10-22 10:45

import datetime
import django.db.models.deletion
from decimal import Decimal
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('ads', '0001_initial'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='AutoRefundUserList',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('auto_refund_enabled', models.BooleanField(default=False)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
        migrations.CreateModel(
            name='Transaction',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('transaction_amount', models.DecimalField(decimal_places=8, max_digits=20)),
                ('price', models.DecimalField(decimal_places=8, max_digits=20)),
                ('fee_percentage', models.DecimalField(decimal_places=2, default=Decimal('1.0'), max_digits=5)),
                ('fiat_currency', models.CharField(choices=[('USD', 'USD'), ('EUR', 'EUR'), ('CHF', 'CHF'), ('RUB', 'RUB'), ('CAD', 'CAD'), ('CNY', 'CNY')], max_length=3)),
                ('payment_methods', models.CharField(max_length=255)),
                ('escrow_wallet_address', models.CharField(blank=True, max_length=255, null=True)),
                ('escrow_released', models.BooleanField(default=False)),
                ('payment_sent', models.BooleanField(default=False)),
                ('status', models.CharField(choices=[('pending', 'Pending'), ('completed', 'Completed'), ('canceled', 'Canceled')], default='pending', max_length=10)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('expires_at', models.DateTimeField(default=datetime.datetime(2024, 10, 22, 12, 15, 4, 124981, tzinfo=datetime.timezone.utc))),
                ('transaction_id', models.CharField(blank=True, max_length=255, null=True, unique=True)),
                ('ad', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='ads.ad')),
                ('buyer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='buyer', to=settings.AUTH_USER_MODEL)),
                ('seller', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='seller', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
