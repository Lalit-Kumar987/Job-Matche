# AWS Resume Scanner & Job Matcher 🚀

Welcome to the **AWS Resume Scanner & Job Matcher**, a cutting-edge serverless web application that revolutionizes the job search experience! Built with the power of AWS cloud technologies, this project seamlessly integrates resume parsing, intelligent job matching, and real-time notifications, all orchestrated within the constraints of the AWS Learner’s Lab. Whether you're a job seeker looking for your next opportunity or a developer eager to explore advanced cloud solutions, this repository offers a scalable, efficient, and innovative solution that showcases the future of career services.

## Project Overview 🌟

This project is a testament to modern cloud architecture, leveraging AWS services like Lambda, S3, DynamoDB, Textract, and SNS to create a robust platform. Users can upload resumes, which are processed to extract key details (e.g., skills, education) using Amazon Textract, matched against job postings via Open AI embeddings, and displayed instantly on a React-based frontend hosted on S3. Daily job aggregation from the JSearch API and email notifications via SNS enhance the user experience, all while adapting to lab limitations by replacing SageMaker with Open AI and forgoing CloudFront for S3 hosting.

### Key Features ✨
- Secure user authentication with Amazon Cognito.
- Real-time resume parsing and job matching using Textract and Open AI.
- Daily job updates via Event Bridge and automated email notifications.
- Scalable serverless architecture aligned with AWS Well-Architected Framework.
- Cost-efficient design, optimized for the AWS Learner’s Lab environment.

## Getting Started 🎉

Ready to dive into this innovative solution? Follow these steps to deploy and run the project on your AWS environment. Let’s bring the architecture to life with ease and precision!

### Prerequisites 🛠️
- An AWS account with access to the Learner’s Lab.
- AWS CLI configured with appropriate credentials.
- Node.js and npm installed for the React frontend (optional for local testing).
- Git installed to clone this repository.

### Installation and Deployment Instructions 📋

1. **Clone the Repository**  
   Start by cloning this repository to your local machine:
       git clone https://github.com/your-username/aws-resume-scanner-job-matcher.git
       cd aws-resume-scanner-job-matcher

2. **Create an S3 Bucket**  
   Create a dedicated S3 bucket to store Lambda code and layers:
   - Open the AWS Management Console and navigate to S3.
   - Click "Create Bucket," name it (e.g., `resume-lambda-bucket-${your-initials}`), and ensure it’s in your region (e.g., us-east-1).
   - Leave default settings, uncheck "Block all public access" (for lab purposes), and create the bucket.

3. **Prepare and Upload Lambda Files**  
   - Locate the `lambdas` folder in the repository, which contains your Lambda functions (e.g., `upload_handler.py`, `textract_processor.py`) and layers (if any) as ZIP files.
   - Upload each ZIP file to the S3 bucket created above via the AWS Console or CLI:
       aws s3 cp lambdas/*.zip s3://resume-lambda-bucket-${your-initials}/
   - Note the S3 paths (e.g., `s3://resume-lambda-bucket-${your-initials}/upload_handler.zip`) for stack configuration.

4. **Organize Infrastructure as Code (IaC)**  
   - Ensure all YAML configuration files (e.g., `main-stack.yaml`, `storage.yaml`) are placed in the `iac` folder within the repository. These files define your CloudFormation stacks for S3, Lambda, DynamoDB, and more.

5. **Deploy the Main Stack**  
   - Navigate to the `iac` folder:
       cd iac
   - Deploy the main CloudFormation stack using the AWS CLI, replacing `<your-stack-name>` with a unique name:
       aws cloudformation deploy --template-file main-stack.yaml --stack-name <your-stack-name> --capabilities CAPABILITY_NAMED_IAM
   - Monitor the stack creation in the AWS Console under CloudFormation, ensuring all resources (e.g., S3 buckets, Lambdas) are successfully provisioned.

6. **Verify and Test**  
   - Access the React frontend via the S3 bucket URL (e.g., `http://resume-output-${your-initials}.s3-website-us-east-1.amazonaws.com`).
   - Upload a resume, check the DynamoDB tables for data, and verify email notifications via SNS.

### Troubleshooting Tips 🔧
- If deployment fails, check CloudFormation events for errors (e.g., IAM permissions) and ensure S3 bucket names are unique.
- For Lambda issues, verify ZIP file contents and S3 paths in the stack configuration.

## Acknowledgments 🙏

Special thanks to the AWS Learner’s Lab team and the xAI community for inspiration and support in crafting this innovative solution.

---

Get started today and experience the power of serverless job matching! 🌐