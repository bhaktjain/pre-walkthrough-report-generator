# Power Automate Integration Guide
## Pre-Walkthrough Report Generator

**Version**: 1.0.0  
**Last Updated**: November 25, 2025

---

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Flow Templates](#flow-templates)
4. [Custom Connector Setup](#custom-connector-setup)
5. [Common Scenarios](#common-scenarios)
6. [Troubleshooting](#troubleshooting)

---

## Overview

This guide provides step-by-step instructions for integrating the Pre-Walkthrough Report Generator with Microsoft Power Automate, enabling automated report generation from various triggers.

### Benefits
- **Zero-code automation**: No programming required
- **Multiple triggers**: Email, SharePoint, scheduled, manual
- **Seamless integration**: Works with Microsoft 365 ecosystem
- **Error handling**: Built-in retry and notification logic

---

## Prerequisites

### Required
- Microsoft 365 account with Power Automate license
- Access to deployed API endpoint (e.g., https://your-app.onrender.com)
- SharePoint site (for file-based flows)
- Outlook/Exchange email (for email-based flows)

### Optional
- Power Automate Premium license (for premium connectors)
- Azure subscription (for advanced features)

---

## Flow Templates

### Template 1: Email-to-Report Automation

**Use Case**: Automatically generate reports when transcript emails arrive

**Trigger**: When a new email arrives (V3)

**Steps**:

#### Step 1: Configure Email Trigger


1. Add trigger: **When a new email arrives (V3)**
2. Configure:
   - **Folder**: Inbox
   - **Include Attachments**: Yes
   - **Subject Filter**: Contains "Transcript" OR "Pre-Walk"
   - **Importance**: Any

#### Step 2: Check for Attachments

1. Add action: **Condition**
2. Configure:
   - **Value**: `length(triggerOutputs()?['body/attachments'])`
   - **Operator**: is greater than
   - **Value**: 0

#### Step 3: Process Each Attachment

1. Add action (in "Yes" branch): **Apply to each**
2. Configure:
   - **Select an output**: `Attachments` (from trigger)

#### Step 4: Filter Text Files

1. Add action (inside Apply to each): **Condition**
2. Configure:
   - **Value**: `items('Apply_to_each')?['name']`
   - **Operator**: ends with
   - **Value**: `.txt`

#### Step 5: Call API

1. Add action (in "Yes" branch): **HTTP**
2. Configure:
   - **Method**: POST
   - **URI**: `https://your-app.onrender.com/generate-report-from-text`
   - **Headers**:
     ```json
     {
       "Content-Type": "application/json"
     }
     ```
   - **Body**:
     ```json
     {
       "transcript_text": "@{base64ToString(items('Apply_to_each')?['contentBytes'])}",
       "address": "@{triggerOutputs()?['body/subject']}",
       "last_name": "@{split(triggerOutputs()?['body/from'], '@')[0]}"
     }
     ```

#### Step 6: Send Report Email

1. Add action: **Send an email (V2)**
2. Configure:
   - **To**: `@{triggerOutputs()?['body/from']}`
   - **Subject**: `Pre-Walkthrough Report - @{triggerOutputs()?['body/subject']}`
   - **Body**:
     ```
     Hello,

     Your pre-walkthrough report has been generated and is attached to this email.

     Property: @{triggerOutputs()?['body/subject']}
     Generated: @{utcNow()}

     Best regards,
     Automated Report System
     ```
   - **Attachments**:
     - **Name**: `PreWalkReport_@{utcNow('yyyyMMdd')}.docx`
     - **Content**: `@{body('HTTP')}`

#### Step 7: Error Handling

1. Configure **HTTP** action settings:
   - Click "..." → **Settings**
   - **Timeout**: PT5M (5 minutes)
   - **Retry Policy**:
     - **Type**: Exponential
     - **Count**: 4
     - **Interval**: PT10S

2. Add parallel action (configure run after "HTTP" has failed):
   - **Send an email (V2)**
   - **To**: Admin email
   - **Subject**: `Report Generation Failed`
   - **Body**:
     ```
     Error generating report for: @{triggerOutputs()?['body/subject']}
     
     Error: @{body('HTTP')?['detail']}
     Timestamp: @{utcNow()}
     ```

---

### Template 2: SharePoint Folder Monitor

**Use Case**: Auto-generate reports when transcripts are uploaded to SharePoint

**Trigger**: When a file is created (properties only)

#### Step 1: Configure SharePoint Trigger

1. Add trigger: **When a file is created (properties only)**
2. Configure:
   - **Site Address**: Your SharePoint site URL
   - **Library Name**: Documents
   - **Folder**: /Transcripts/Pending

#### Step 2: Get File Content

1. Add action: **Get file content**
2. Configure:
   - **Site Address**: Same as trigger
   - **File Identifier**: `triggerOutputs()?['body/{Identifier}']`

#### Step 3: Parse Filename

1. Add action: **Compose**
2. Configure:
   - **Inputs**: `split(triggerOutputs()?['body/{FilenameWithExtension}'], '.')[0]`
3. Rename to: "Extract Filename"

#### Step 4: Call API

1. Add action: **HTTP**
2. Configure:
   - **Method**: POST
   - **URI**: `https://your-app.onrender.com/generate-report-from-text`
   - **Headers**:
     ```json
     {
       "Content-Type": "application/json"
     }
     ```
   - **Body**:
     ```json
     {
       "transcript_text": "@{body('Get_file_content')}",
       "last_name": "@{outputs('Extract_Filename')}"
     }
     ```

#### Step 5: Save Report to SharePoint

1. Add action: **Create file**
2. Configure:
   - **Site Address**: Same as trigger
   - **Folder Path**: /Reports
   - **File Name**: `PreWalk_@{outputs('Extract_Filename')}_@{utcNow('yyyyMMdd')}.docx`
   - **File Content**: `@{body('HTTP')}`

#### Step 6: Move Processed File

1. Add action: **Move file**
2. Configure:
   - **Site Address**: Same as trigger
   - **Current Folder**: /Transcripts/Pending
   - **File to Move**: `triggerOutputs()?['body/{Identifier}']`
   - **Destination Folder**: /Transcripts/Processed

#### Step 7: Send Notification

1. Add action: **Send an email (V2)**
2. Configure:
   - **To**: Team email
   - **Subject**: `New Report Generated: @{outputs('Extract_Filename')}`
   - **Body**:
     ```
     A new pre-walkthrough report has been generated and saved to SharePoint.

     Report: @{outputs('Create_file')?['body/{Name}']}
     Location: @{outputs('Create_file')?['body/{Link}']}
     Generated: @{utcNow()}

     Original transcript moved to Processed folder.
     ```

---

### Template 3: Scheduled Batch Processing

**Use Case**: Process all pending transcripts daily at a specific time

**Trigger**: Recurrence

#### Step 1: Configure Recurrence Trigger

1. Add trigger: **Recurrence**
2. Configure:
   - **Interval**: 1
   - **Frequency**: Day
   - **Time zone**: Your timezone
   - **At these hours**: 9
   - **At these minutes**: 0

#### Step 2: List Pending Files

1. Add action: **List files in folder**
2. Configure:
   - **Site Address**: Your SharePoint site
   - **Library**: Documents
   - **Folder**: /Transcripts/Pending

#### Step 3: Initialize Counter

1. Add action: **Initialize variable**
2. Configure:
   - **Name**: ProcessedCount
   - **Type**: Integer
   - **Value**: 0

#### Step 4: Process Each File

1. Add action: **Apply to each**
2. Configure:
   - **Select an output**: `value` (from List files)

3. Inside loop, add:
   - **Get file content**
   - **HTTP** (call API)
   - **Create file** (save report)
   - **Move file** (to Processed folder)
   - **Increment variable** (ProcessedCount)

#### Step 5: Send Summary Email

1. Add action (after Apply to each): **Send an email (V2)**
2. Configure:
   - **To**: Admin email
   - **Subject**: `Daily Report Generation Complete - @{utcNow('yyyy-MM-dd')}`
   - **Body**:
     ```
     Daily batch processing completed successfully.

     Files processed: @{variables('ProcessedCount')}
     Start time: @{triggerOutputs()?['body/startTime']}
     End time: @{utcNow()}

     All reports saved to /Reports folder.
     All transcripts moved to /Transcripts/Processed.
     ```

---

### Template 4: Manual Trigger with Form

**Use Case**: On-demand report generation with user input

**Trigger**: Manually trigger a flow

#### Step 1: Configure Manual Trigger

1. Add trigger: **Manually trigger a flow**
2. Add inputs:
   - **Transcript Text** (Text, Multi-line, Required)
   - **Property Address** (Text, Optional)
   - **Client Last Name** (Text, Optional)

#### Step 2: Call API

1. Add action: **HTTP**
2. Configure:
   - **Method**: POST
   - **URI**: `https://your-app.onrender.com/generate-report-from-text`
   - **Headers**:
     ```json
     {
       "Content-Type": "application/json"
     }
     ```
   - **Body**:
     ```json
     {
       "transcript_text": "@{triggerBody()?['text']}",
       "address": "@{triggerBody()?['text_1']}",
       "last_name": "@{triggerBody()?['text_2']}"
     }
     ```

#### Step 3: Save to OneDrive

1. Add action: **Create file**
2. Configure:
   - **Folder Path**: /Reports
   - **File Name**: `PreWalk_@{triggerBody()?['text_2']}_@{utcNow('yyyyMMdd_HHmmss')}.docx`
   - **File Content**: `@{body('HTTP')}`

#### Step 4: Notify User

1. Add action: **Send me an email notification**
2. Configure:
   - **Subject**: `Report Generated Successfully`
   - **Body**:
     ```
     Your pre-walkthrough report has been generated.

     File: @{outputs('Create_file')?['body/Name']}
     Location: @{outputs('Create_file')?['body/Path']}

     Click here to open: @{outputs('Create_file')?['body/WebUrl']}
     ```

---

## Custom Connector Setup

### Creating a Custom Connector

#### Step 1: Navigate to Custom Connectors

1. Go to https://make.powerautomate.com
2. Click **Data** → **Custom connectors**
3. Click **+ New custom connector** → **Create from blank**

#### Step 2: General Information

1. **Connector name**: Pre-Walkthrough Report Generator
2. **Description**: Generates comprehensive pre-walkthrough reports from renovation consultation transcripts
3. **Host**: `your-app.onrender.com`
4. **Base URL**: `/`

#### Step 3: Security

1. **Authentication type**: No authentication
   - (Or **API Key** if you implement authentication)

#### Step 4: Definition

##### Action 1: Generate Report from Text

1. Click **+ New action**
2. Configure:
   - **Summary**: Generate Pre-Walkthrough Report
   - **Description**: Generates a comprehensive report from transcript text
   - **Operation ID**: generateReportFromText
   - **Visibility**: important

3. **Request**:
   - **Import from sample**
   - **Verb**: POST
   - **URL**: `https://your-app.onrender.com/generate-report-from-text`
   - **Headers**:
     ```
     Content-Type: application/json
     ```
   - **Body**:
     ```json
     {
       "transcript_text": "Sample transcript...",
       "address": "123 Main St, Brooklyn, NY",
       "last_name": "Smith"
     }
     ```

4. **Response**:
   - **Add default response**
   - **Body**: (Binary file content)

#### Step 5: Test

1. Click **Test** tab
2. Create new connection
3. Test with sample data
4. Verify .docx file is returned

#### Step 6: Save and Use

1. Click **Create connector**
2. Use in flows via **Custom** connectors section

---

## Common Scenarios

### Scenario 1: CRM Integration (Dynamics 365)

**Flow**:
```
Opportunity stage changes to "Site Visit Completed"
    ↓
Get transcript from Notes field
    ↓
Generate report via API
    ↓
Attach report to Opportunity
    ↓
Update stage to "Report Sent"
    ↓
Send notification to sales rep
```

**Implementation**:
1. Trigger: **When a record is updated** (Opportunity)
2. Condition: Stage = "Site Visit Completed"
3. Get Notes field content
4. HTTP: Call API
5. **Add attachment to record**
6. **Update record** (Stage = "Report Sent")
7. **Send email** to owner

### Scenario 2: Teams Integration

**Flow**:
```
Message posted in Teams channel
    ↓
Extract transcript from message
    ↓
Generate report
    ↓
Post report back to channel
```

**Implementation**:
1. Trigger: **When a new channel message is added**
2. Condition: Message contains "@ReportBot"
3. Parse message content
4. HTTP: Call API
5. **Post message in a chat or channel** with file attachment

### Scenario 3: Multi-Language Support

**Flow**:
```
Receive transcript in any language
    ↓
Detect language (Azure Cognitive Services)
    ↓
Translate to English if needed
    ↓
Generate report
    ↓
Translate report back to original language
    ↓
Send to client
```

**Implementation**:
1. Trigger: Email arrives
2. **Detect Language** (Azure Cognitive Services)
3. Condition: If language != English
4. **Translate Text** to English
5. HTTP: Generate report
6. **Translate Text** back to original language
7. Send email with translated report

---

## Troubleshooting

### Issue 1: "HTTP 400 Bad Request"

**Cause**: Invalid JSON or missing required fields

**Solution**:
1. Check JSON syntax in HTTP body
2. Ensure `transcript_text` is not empty
3. Verify Content-Type header is set
4. Test with Postman first

### Issue 2: "HTTP 500 Internal Server Error"

**Cause**: Server-side processing error

**Solution**:
1. Check server logs
2. Verify API keys are configured
3. Test with shorter transcript
4. Contact support if persistent

### Issue 3: "Timeout Error"

**Cause**: Request taking longer than timeout setting

**Solution**:
1. Increase timeout in HTTP action settings
2. Use async processing pattern
3. Implement status polling

### Issue 4: "File Not Created in SharePoint"

**Cause**: Permissions or path issue

**Solution**:
1. Verify SharePoint permissions
2. Check folder path exists
3. Test with manual file creation
4. Review flow run history for details

### Issue 5: "Email Not Sent"

**Cause**: Email connector configuration

**Solution**:
1. Verify email address format
2. Check mailbox permissions
3. Review email size limits
4. Test with simple email first

---

## Best Practices

### Performance
- Use **Apply to each** with concurrency control (5-10)
- Cache frequently accessed data
- Implement retry logic with exponential backoff
- Set appropriate timeouts (5 minutes for report generation)

### Error Handling
- Always configure "run after" settings
- Send error notifications to admins
- Log errors to SharePoint list
- Implement fallback actions

### Security
- Don't log sensitive information
- Use secure connections (HTTPS)
- Implement access controls
- Rotate API keys regularly

### Monitoring
- Enable flow analytics
- Set up alerts for failures
- Track processing times
- Monitor API usage

---

## Support

For additional help:
- Power Automate Community: https://powerusers.microsoft.com/
- Microsoft Learn: https://learn.microsoft.com/power-automate/
- API Documentation: See main documentation

---

**End of Power Automate Integration Guide**
