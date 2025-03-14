import boto3

sns = boto3.client('sns')

def get_or_create_sns_topic(zip_code):
    """
    Find existing SNS topic for zip code or create a new one.
    Returns the topic ARN.
    """
    topic_name = f"wildfire-alerts-{zip_code}"
    
    # Check if SNS topic already exists
    topics = sns.list_topics().get('Topics', [])
    for topic in topics:
        if topic_name in topic['TopicArn']:
            print(f"Found existing SNS topic for zip code {zip_code}")
            return topic['TopicArn']
    
    # Create a new SNS topic if it doesn't already exist
    try:
        response = sns.create_topic(Name=topic_name)
        print(f"Created new SNS topic for zip code {zip_code}")
        return response['TopicArn']
    except Exception as e:
        print(f"Failed to create SNS topic: {str(e)}")
        raise

def subscribe_user_to_topic(email, topic_arn):
    """
    Subscribe user's email to the SNS topic.
    """
    try:
        response = sns.subscribe(
            TopicArn=topic_arn,
            Protocol='email',
            Endpoint=email
        )
        print(f"Subscribed {email} to SNS topic")
        return response
    except Exception as e:
        print(f"Failed to subscribe user: {str(e)}")
        raise

def send_clustered_alert(fires, email, topic_arn):
    """
    Group nearby fires and send a consolidated alert email.
    """
    if fires.empty:
        return  # No fires to report

    # Create a summary of all fires detected
    fire_summary = "\n".join([
        f"🔥 {row['latitude']:.4f}, {row['longitude']:.4f} - FRP: {row['frp']} MW, Date: {row['acq_date']}"
        for _, row in fires.iterrows()
    ])

    # Construct the email message
    message = (
        f"🔥 Wildfire Alert for Your Area!\n\n"
        f"We have detected {len(fires)} wildfire(s) in your vicinity:\n\n"
        f"{fire_summary}\n\n"
        f"Stay safe and monitor local news for evacuation instructions."
    )

    try:
        sns.publish(TopicArn=topic_arn, Message=message, Subject="🔥 Wildfire Alert - Multiple Fires")
        print(f"✅ Sent alert to {email} with {len(fires)} fires.")
    except Exception as e:
        print(f"❌ Failed to send alert to {email}: {str(e)}")
