from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True
    dependencies = []

    operations = [
        migrations.CreateModel(
            name="OTPCode",
            fields=[
                ("id", models.BigAutoField(auto_created=True, primary_key=True, serialize=False)),
                ("phone", models.CharField(db_index=True, max_length=48)),
                (
                    "purpose",
                    models.CharField(
                        choices=[
                            ("verify_phone", "Verify phone"),
                            ("login", "Login"),
                            ("password_reset", "Password reset"),
                        ],
                        max_length=32,
                    ),
                ),
                (
                    "channel",
                    models.CharField(
                        choices=[("sms", "SMS"), ("whatsapp", "WhatsApp")],
                        default="sms",
                        max_length=16,
                    ),
                ),
                ("code_hash", models.CharField(max_length=128)),
                ("attempts", models.PositiveIntegerField(default=0)),
                ("consumed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("expires_at", models.DateTimeField()),
            ],
            options={
                "ordering": ["-created_at"],
            },
        ),
        migrations.AddIndex(
            model_name="otpcode",
            index=models.Index(
                fields=["phone", "purpose", "-created_at"],
                name="nomadicode__phone_p_idx",
            ),
        ),
    ]
