# Building a Personal Portfolio with Google AI Studio

## 1. Introduction
**Overview**
Where does building with AI start today? For most of us, it starts with a query or prototype. Google AI Studio offers a powerful Build Mode (often referred to as "vibe coding") that lets you design, test, and build web applications using code generation driven by Gemini models.
In this codelab, you will build a personal portfolio website. The AI Studio agent will write the frontend code. Once the app is polished, you will deploy it straight to Cloud Run with a single click.

**What you'll do**
* Prompt Google AI Studio to prototype a personal portfolio website.
* Test the application in the interactive preview sandbox.
* Deploy the application to Cloud Run directly from the Google AI Studio UI.

**What you'll learn**
* How to use Google AI Studio's Build mode to rapidly prototype a frontend service using natural language.
* How to deploy your AI Studio application as a serverless container on Cloud Run.

## 2. Project Setup
Before launching AI Studio, verify your account status and prerequisites.

**Google Account & Tier Information**
If you don't already have a Google Account, create a Google Account. 
> **Tip:** Use a personal Google account for this lab if possible. Group, corporate, or school accounts may enforce Workspace policies that disable experimental features or cloud integrations.

Review the billing details for deployments:
* **Google Cloud Starter Tier:** Allows publishing up to two full-stack applications in a select region at no cost, without establishing a full Google Cloud billing account.
* **Standard Deployment:** Connects to an existing paid Google Cloud project and expands storage limits, CPU resources, and APIs.

## 3. Create a Portfolio Website in AI Studio Build Mode
Create the application shell and prompt the AI code assistant to build the frontend layout.
1. Navigate to Google AI Studio Apps panel and click **New App**.
2. In the chat prompt box, enter the description for your portfolio application:
   > Build a professional personal portfolio website. The site should have a modern, responsive design and sections for my biography, projects showcase, skills, and links to my professional profiles (e.g., GitHub, LinkedIn).
   
   *(Note: This [link](https://aistudio.google.com/apps?prompt=Build%20a%20professional%20personal%20portfolio%20website.%20The%20site%20should%20have%20a%20modern%2C%20responsive%20design%20and%20sections%20for%20my%20biography%2C%20projects%20showcase%2C%20skills%2C%20and%20links%20to%20my%20professional%20profiles%20%28e.g.%2C%20GitHub%2C%20LinkedIn%29) will automatically fill the prompt box for you.)*
3. Click **Build** to start the application generation process.

## 4. Test and Iterate
Before launching the service live, run validation checks in the interactive preview.
1. Open the preview pane inside Google AI Studio.
2. Interact with any navigation buttons, links, or layouts in the preview sandbox to verify the visual experience.
   > **Note on fixing errors:** During generation or testing, you might occasionally face runtime issues or compilation errors. If this happens, AI Studio displays a **Fix** button in the chat, allowing you to ask the agent to automatically diagnose and repair the issue.
3. If you want to change styling or behavior, instruct the agent through the chat window. For example:
   * *"Could you style the interface using Tailwind CSS, and add a dark mode toggle button?"*
   * *"Include a new section to showcase my recent presentations and talks."*
4. Wait for the agent to update the codebase and check the preview browser to see the updates.

## 5. Deploy to Cloud Run
Once your prototype is fully functional, deploy it as a public service on Cloud Run.
1. In the top-right corner of Google AI Studio, click the **Publish** button to initiate the deployment wizard. 
   ![Publish Button](image_379a33.png)
2. Click **Get Started** to configure your Google Cloud project. Verify the target Google Cloud Project drop-down matches the project you associated with your workspace.
   * AI Studio will automatically generate a unique service identifier for the Cloud Run instance.
   * Optionally, you can specify a custom `.ai.studio` URL prefix (e.g., `your-portfolio-name.ai.studio`) as part of your deployment configuration.
   * If this is your first time deploying and you are using standard Google Cloud parameters, you may be prompted to specify an organization type and supply billing details.
3. Click **Publish App**.
4. The container build, container registration, and service deployment steps happen in the background. This process normally completes in 2–4 minutes.
5. When deployment finishes, copy the generated App URL and visit the live application link in a browser tab.
6. Test the live web application in your browser!

## 6. (OPTIONAL) Add a custom domain
By default, Cloud Run hosts your service on a Google-managed `run.app` subdomain. If you want to use a personal domain (like `yourname.com` or `portfolio.yourname.com`), you can map a custom domain to your service.

**Step 1: Add a domain mapping in Cloud Run**
1. Go to the Cloud Run Domain Mappings page in the Google Cloud Console.
2. Click **Add Mapping**.
3. Choose the Cloud Run service you want to map from the drop-down.
4. Input your custom domain name (for example, `yourname.com` or `portfolio.yourname.com`).
5. Click **Next** or **Continue**. Cloud Run will display the DNS records (such as A/AAAA or CNAME records) that you must create with your domain registrar.

**Step 2: Configure your DNS registrar**
1. Sign in to your domain registrar's administration panel (for example, Squarespace, GoDaddy, or Namecheap).
2. Open the DNS management or DNS settings configuration page for your domain.
3. Create the DNS records matching the values shown in the Cloud Run mapping wizard:
   * For apex domain mappings (e.g., `yourname.com`), add the listed A and AAAA records.
   * For subdomain mappings (e.g., `portfolio.yourname.com`), add the listed CNAME record.
4. Save the DNS configuration changes.

**Step 3: Wait for SSL certificate provisioning**
Once the DNS changes propagate:
* Google Cloud will automatically provision a managed SSL/TLS certificate for your secure connection.
* This process usually completes in about 15 minutes but can take up to 24 hours depending on DNS propagation.
* Once completed, your custom domain will route safely to your portfolio website.

## 7. Clean Up
To avoid any unforeseen billing charges or clean up your workspace resources:
1. In Google AI Studio, go to the Apps page.
2. Find your application in the grid or list.
3. Click the trash icon to delete the app state and unpublish the service from Cloud Run.
4. If you deployed using a standard project and want to shut down all resources entirely, go to the Google Cloud Console Project Settings and delete the underlying project.

## 8. Conclusion
Congratulations! You have designed, developed, and deployed a portfolio website directly from Google AI Studio.
