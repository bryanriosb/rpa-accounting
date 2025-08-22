'use server'

import { SQSClient, SendMessageCommand } from '@aws-sdk/client-sqs'

const sqsClient = new SQSClient({
  region: process.env.AWS_REGION || 'us-west-1',
  credentials: {
    accessKeyId: process.env.AWS_ACCESS_KEY_ID!,
    secretAccessKey: process.env.AWS_SECRET_ACCESS_KEY!,
  },
})

export interface SQSMessage {
  messageBody: string
  messageGroupId?: string
  messageDeduplicationId?: string
  messageAttributes?: Record<string, any>
}

export interface ExecutionQueueMessage {
  portals: string[]
  targetDate: string
  executionId: string
  timestamp: string
}

export async function sendMessageToSQS(
  queueUrl: string,
  message: SQSMessage
): Promise<{ success: boolean; messageId?: string; error?: string }> {
  try {
    const command = new SendMessageCommand({
      QueueUrl: queueUrl,
      MessageBody: message.messageBody,
      MessageGroupId: message.messageGroupId,
      MessageDeduplicationId: message.messageDeduplicationId,
      MessageAttributes: message.messageAttributes,
    })

    const result = await sqsClient.send(command)

    return {
      success: true,
      messageId: result.MessageId,
    }
  } catch (error) {
    console.error('Error sending message to SQS:', error)
    return {
      success: false,
      error: error instanceof Error ? error.message : 'Unknown error',
    }
  }
}

export async function sendExecutionToQueue(
  executionData: ExecutionQueueMessage
): Promise<{ success: boolean; messageId?: string; error?: string }> {
  const queueUrl = process.env.SQS_QUEUE_URL

  if (!queueUrl) {
    return {
      success: false,
      error: 'SQS_QUEUE_URL environment variable is not configured',
    }
  }

  const messageBody = JSON.stringify(executionData)

  // Generate unique IDs for FIFO queue
  const timestamp = Date.now().toString()
  const messageGroupId = 'credit-notes-execution'
  const messageDeduplicationId = `${executionData.executionId}-${timestamp}`

  return await sendMessageToSQS(queueUrl, {
    messageBody,
    messageGroupId,
    messageDeduplicationId,
    messageAttributes: {
      executionId: {
        StringValue: executionData.executionId,
        DataType: 'String',
      },
      targetDate: {
        StringValue: executionData.targetDate,
        DataType: 'String',
      },
      portalsCount: {
        StringValue: executionData.portals.length.toString(),
        DataType: 'Number',
      },
    },
  })
}

export async function sendPortalExecutionToQueue(
  portals: string[],
  targetDate: string
): Promise<{ success: boolean; messageId?: string; error?: string }> {
  const executionId = `exec-${Date.now()}-${Math.random()
    .toString(36)
    .substr(2, 9)}`

  const executionData: ExecutionQueueMessage = {
    portals,
    targetDate,
    executionId,
    timestamp: new Date().toISOString(),
  }

  return await sendExecutionToQueue(executionData)
}
