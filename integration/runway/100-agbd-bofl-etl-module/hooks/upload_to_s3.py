import glob
import os
from pathlib import Path
import shutil
import boto3


def hook(provider, context, **kwargs):
    """validate module config"""
    print(
        "arguments being used:",
        "local_dir: ",
        kwargs["local_dir"],
        "aws_init_dir: ",
        kwargs["aws_init_dir"],
        "bucket_name: ",
        kwargs["bucket_name"],
        "tag: ",
        kwargs["tag"],
        "zip",
        kwargs["zip"],
    )
    return upload_to_s3(
        kwargs["local_dir"],
        kwargs["aws_init_dir"],
        kwargs["bucket_name"],
        kwargs["tag"],
        kwargs["zip"],
    )


def upload_to_s3(local_dir, aws_init_dir, bucket_name, tag, zip: bool, prefix="/"):
    s3 = boto3.resource("s3")
    cwd = str(Path.cwd())
    p = Path(os.path.join(Path.cwd(), local_dir))

    jar_urls = []
    if zip:
        # Create zip file
        zip_name = local_dir[:-1]  # Remove trailing slash
        zip_file = shutil.make_archive(zip_name, "zip", cwd, zip_name)
        print(f"Created zip file: {zip_file}")

        # Upload the zip file to S3 inside a folder with the same name
        zip_s3_key = f"{aws_init_dir}/{os.path.basename(zip_file)[:-4]}/{os.path.basename(zip_file)}"
        print(f"Uploading {zip_file} to s3://{bucket_name}/{zip_s3_key}")
        s3.meta.client.upload_file(zip_file, bucket_name, zip_s3_key)

        # If you still want to build and upload the wheel file
        os.system("poetry build")
        mydirs = list(Path.cwd().glob("./dist/*"))
        if len(mydirs) > 1:  # Make sure we have files in dist
            file_name = mydirs[1]  # gets .whl only
            aws_path = str(file_name).replace(cwd, "").replace("..", "")
            aws_path = aws_path.replace(prefix, "", 1)
            s3.meta.client.upload_file(
                file_name,
                bucket_name,
                f"{aws_init_dir}/{local_dir[:-1]}/{aws_path[5:]}",
            )

    # Rest of your existing code
    mydirs = list(p.glob("**"))
    for mydir in mydirs:
        file_names = glob.glob(os.path.join(mydir, tag))
        file_names = [f for f in file_names if not Path(f).is_dir()]
        for _, file_name in enumerate(file_names):
            aws_path = str(file_name).replace(cwd, "").replace("..", "")
            aws_path = aws_path.replace(prefix, "", 1)
            print(f"file_name {file_name}, awsPath {aws_init_dir}/{aws_path}")

            s3.meta.client.upload_file(
                file_name, bucket_name, f"{aws_init_dir}/{aws_path}"
            )
            if file_name.split(".")[-1] == "jar":
                jar_urls.append(f"s3://{bucket_name}/{aws_init_dir}/{aws_path}")

    return {"jarUrls": ",".join(jar_urls)}
