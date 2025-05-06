import boto3
import botocore.exceptions

sns = boto3.client("sns")


def get_or_create_sns_topic(zip_code):
    """Find existing SNS topic for zip code or create a new one."""
    if not zip_code or not zip_code.strip().isdigit():
        raise ValueError(f"Invalid zip code: {zip_code}")

    topic_name = f"wildfire-alerts-{zip_code}"

    try:
        paginator = sns.get_paginator("list_topics")
        for page in paginator.paginate():
            for topic in page.get("Topics", []):
                arn = topic.get("TopicArn", "")
                if arn.endswith(f":{topic_name}"):
                    print(f"Found existing SNS topic: {arn}")
                    return arn

        # If not found, create a new topic
        response = sns.create_topic(Name=topic_name)
        topic_arn = response["TopicArn"]
        print(f"🆕 Created new SNS topic: {topic_arn}")
        return topic_arn

    except botocore.exceptions.ClientError as e:
        print(f"SNS client error during topic lookup/creation: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error in get_or_create_sns_topic: {e}")
        raise


def subscribe_user_to_topic(email, topic_arn):
    """Subscribe user's email to the SNS topic."""
    if not email or "@" not in email:
        raise ValueError(f"Invalid email address: {email}")
    if not topic_arn or not topic_arn.startswith("arn:aws:sns"):
        raise ValueError(f"Invalid SNS topic ARN: {topic_arn}")

    try:
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol="email",
            Endpoint=email
        )
        print(f"📬 Subscribed {email} to SNS topic {topic_arn}")
        return response
    except botocore.exceptions.ClientError as e:
        print(f"Failed to subscribe {email}: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error subscribing user: {e}")
        raise


def send_clustered_alert(fires, email, topic_arn):
    """Group nearby fires and send a consolidated alert per cluster."""
    if fires.empty:
        print("No fires to alert.")
        return

    clusters = {}
    GRID_SIZE = 0.0725  # ~5 miles in degrees

    for _, fire in fires.iterrows():
        try:
            lat = float(fire["latitude"])
            lon = float(fire["longitude"])
            grid_lat = round(lat / GRID_SIZE) * GRID_SIZE
            grid_lon = round(lon / GRID_SIZE) * GRID_SIZE
            grid_key = f"{grid_lat},{grid_lon}"

            clusters.setdefault(grid_key, {
                "center": (grid_lat, grid_lon),
                "fires": []
            })["fires"].append(fire)
        except (KeyError, ValueError) as e:
            print(f"Skipping invalid fire record: {e}")
            continue

    alert_messages = []
    for cluster in clusters.values():
        if not cluster["fires"]:
            continue
        fire = cluster["fires"][0]
        message = (
            f"🔥 Wildfire Alert!\n"
            f"Location: {cluster['center'][0]:.4f}, {cluster['center'][1]:.4f}\n"
            f"Number of fires in cluster: {len(cluster['fires'])}\n"
            f"Fire Radiative Power: {fire.get('frp', 'N/A')} MW\n"
            f"Date: {fire.get('acq_date', 'Unknown')}"
        )
        alert_messages.append(message)

    final_alert = "\n\n".join(alert_messages)

    try:
        sns.publish(
            TopicArn=topic_arn,
            Message=final_alert,
            Subject="🔥 Wildfire Alert"
        )
        print(f"Alert sent to {email} with {len(clusters)} fire clusters.")
    except botocore.exceptions.ClientError as e:
        print(f"Failed to send alert to {email}: {e}")
        raise
    except Exception as e:
        print(f"Unexpected error sending alert: {e}")
        raise
