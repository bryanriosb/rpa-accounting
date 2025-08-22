'use server'

import { DynamoDBClient } from '@aws-sdk/client-dynamodb'
import {
  DynamoDBDocumentClient,
  ScanCommand,
  QueryCommand,
  GetCommand,
  ScanCommandInput,
  QueryCommandInput,
  GetCommandInput,
} from '@aws-sdk/lib-dynamodb'

let client: DynamoDBDocumentClient

const accessKeyId = process.env.AWS_ACCESS_KEY_ID!
const secretAccessKey = process.env.AWS_SECRET_ACCESS_KEY!
const region = process.env.AWS_REGION!
const dynamoClient = new DynamoDBClient({
  region,
  credentials: {
    accessKeyId,
    secretAccessKey,
  },
})

client = DynamoDBDocumentClient.from(dynamoClient)

export async function scanTable<T = any>(
  tableName: string,
  options?: {
    limit?: number
    filterExpression?: string
    expressionAttributeNames?: Record<string, string>
    expressionAttributeValues?: Record<string, any>
    lastEvaluatedKey?: Record<string, any>
  }
): Promise<{ items: T[]; lastEvaluatedKey?: Record<string, any> }> {
  try {
    const params: ScanCommandInput = {
      TableName: tableName,
      Limit: options?.limit,
      FilterExpression: options?.filterExpression,
      ExpressionAttributeNames: options?.expressionAttributeNames,
      ExpressionAttributeValues: options?.expressionAttributeValues,
      ExclusiveStartKey: options?.lastEvaluatedKey,
    }

    const command = new ScanCommand(params)
    const result = await client.send(command)

    return {
      items: (result.Items as T[]) || [],
      lastEvaluatedKey: result.LastEvaluatedKey,
    }
  } catch (error) {
    console.error('Error scanning DynamoDB table:', error)
    throw error
  }
}

export async function queryTable<T = any>(
  tableName: string,
  options: {
    keyConditionExpression: string
    expressionAttributeNames?: Record<string, string>
    expressionAttributeValues: Record<string, any>
    filterExpression?: string
    indexName?: string
    limit?: number
    lastEvaluatedKey?: Record<string, any>
    scanIndexForward?: boolean
  }
): Promise<{ items: T[]; lastEvaluatedKey?: Record<string, any> }> {
  try {
    const params: QueryCommandInput = {
      TableName: tableName,
      KeyConditionExpression: options.keyConditionExpression,
      ExpressionAttributeNames: options.expressionAttributeNames,
      ExpressionAttributeValues: options.expressionAttributeValues,
      FilterExpression: options.filterExpression,
      IndexName: options.indexName,
      Limit: options.limit,
      ExclusiveStartKey: options.lastEvaluatedKey,
      ScanIndexForward: options.scanIndexForward,
    }

    const command = new QueryCommand(params)
    const result = await client.send(command)

    return {
      items: (result.Items as T[]) || [],
      lastEvaluatedKey: result.LastEvaluatedKey,
    }
  } catch (error) {
    console.error('Error querying DynamoDB table:', error)
    throw error
  }
}

export async function getItem<T = any>(
  tableName: string,
  key: Record<string, any>
): Promise<T | null> {
  try {
    const params: GetCommandInput = {
      TableName: tableName,
      Key: key,
    }

    const command = new GetCommand(params)
    const result = await client.send(command)

    return (result.Item as T) || null
  } catch (error) {
    console.error('Error getting item from DynamoDB:', error)
    throw error
  }
}

export async function queryAllItems<T = any>(
  tableName: string,
  options: {
    keyConditionExpression: string
    expressionAttributeNames?: Record<string, string>
    expressionAttributeValues: Record<string, any>
    filterExpression?: string
    indexName?: string
    scanIndexForward?: boolean
  }
): Promise<T[]> {
  const items: T[] = []
  let lastEvaluatedKey: Record<string, any> | undefined

  do {
    const result = await queryTable<T>(tableName, {
      ...options,
      lastEvaluatedKey,
    })

    items.push(...result.items)
    lastEvaluatedKey = result.lastEvaluatedKey
  } while (lastEvaluatedKey)

  return items
}

export async function getAllItems<T = any>(
  tableName: string,
  options?: {
    filterExpression?: string
    expressionAttributeNames?: Record<string, string>
    expressionAttributeValues?: Record<string, any>
  }
): Promise<T[]> {
  const items: T[] = []
  let lastEvaluatedKey: Record<string, any> | undefined

  do {
    const result = await scanTable<T>(tableName, {
      ...options,
      lastEvaluatedKey,
    })

    items.push(...result.items)
    lastEvaluatedKey = result.lastEvaluatedKey
  } while (lastEvaluatedKey)

  return items
}

export async function getAllItemsOrderedByCreatedAt<T = any>(
  tableName: string,
  options?: {
    filterExpression?: string
    expressionAttributeNames?: Record<string, string>
    expressionAttributeValues?: Record<string, any>
    limit?: number
    descending?: boolean
  }
): Promise<T[]> {
  try {
    // Obtener todos los elementos
    const items = await getAllItems<T>(tableName, {
      filterExpression: options?.filterExpression,
      expressionAttributeNames: options?.expressionAttributeNames,
      expressionAttributeValues: options?.expressionAttributeValues,
    })

    // Ordenar por createdAt
    const sortedItems = items.sort((a: any, b: any) => {
      const dateA = new Date(a.createdAt || 0).getTime()
      const dateB = new Date(b.createdAt || 0).getTime()
      
      // Por defecto descendente (más reciente primero)
      return options?.descending === false ? dateA - dateB : dateB - dateA
    })

    // Aplicar límite si se especifica
    return options?.limit ? sortedItems.slice(0, options.limit) : sortedItems
  } catch (error) {
    console.error('Error getting items ordered by createdAt:', error)
    throw error
  }
}

export async function queryByCreatedAtIndex<T = any>(
  tableName: string,
  options: {
    indexName: string
    partitionKey?: string
    partitionKeyValue?: any
    startDate?: string
    endDate?: string
    limit?: number
    descending?: boolean
  }
): Promise<T[]> {
  try {
    let keyConditionExpression: string
    const expressionAttributeNames: Record<string, string> = {}
    const expressionAttributeValues: Record<string, any> = {}

    // Si hay partition key, usarla
    if (options.partitionKey && options.partitionKeyValue) {
      keyConditionExpression = `#pk = :pkval`
      expressionAttributeNames['#pk'] = options.partitionKey
      expressionAttributeValues[':pkval'] = options.partitionKeyValue

      // Agregar condición de rango para createdAt
      if (options.startDate || options.endDate) {
        expressionAttributeNames['#createdAt'] = 'createdAt'
        
        if (options.startDate && options.endDate) {
          keyConditionExpression += ` AND #createdAt BETWEEN :startDate AND :endDate`
          expressionAttributeValues[':startDate'] = options.startDate
          expressionAttributeValues[':endDate'] = options.endDate
        } else if (options.startDate) {
          keyConditionExpression += ` AND #createdAt >= :startDate`
          expressionAttributeValues[':startDate'] = options.startDate
        } else if (options.endDate) {
          keyConditionExpression += ` AND #createdAt <= :endDate`
          expressionAttributeValues[':endDate'] = options.endDate
        }
      }
    } else {
      // Solo consulta por createdAt como partition key del índice
      keyConditionExpression = `#createdAt >= :startDate`
      expressionAttributeNames['#createdAt'] = 'createdAt'
      expressionAttributeValues[':startDate'] = options.startDate || '2020-01-01'
    }

    return await queryAllItems<T>(tableName, {
      keyConditionExpression,
      expressionAttributeNames,
      expressionAttributeValues,
      indexName: options.indexName,
      scanIndexForward: options.descending === false, // false = descendente
    })
  } catch (error) {
    console.error('Error querying by createdAt index:', error)
    throw error
  }
}
