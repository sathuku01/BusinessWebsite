import os

from django.core.management.base import BaseCommand

import cloudinary


class Command(BaseCommand):
    help = "Show Cloudinary configuration status (never prints secrets)"

    def handle(self, *args, **options):
        env_vars = sorted(name for name in os.environ if name.startswith("CLOUDINARY"))
        self.stdout.write(
            f"CLOUDINARY_* env vars present: {', '.join(env_vars) or 'none'}"
        )
        self.stdout.write(
            "CLOUDINARY_URL present: "
            f"{'yes' if os.environ.get('CLOUDINARY_URL') else 'no'}"
        )

        config = cloudinary.config()
        self.stdout.write(f"cloud_name: {config.cloud_name or 'NOT SET'}")
        self.stdout.write(f"api_key set: {'yes' if config.api_key else 'no'}")
        self.stdout.write(f"api_secret set: {'yes' if config.api_secret else 'no'}")

        if config.cloud_name and config.api_key and config.api_secret:
            self.stdout.write(self.style.SUCCESS("Cloudinary is configured."))
        else:
            self.stdout.write(self.style.ERROR(
                "Cloudinary is NOT configured. Set exactly one variable, "
                "CLOUDINARY_URL=cloudinary://API_KEY:API_SECRET@CLOUD_NAME"
            ))
