import { defineCollection, z } from 'astro:content';
import { glob } from 'astro/loaders';

const issues = defineCollection({
  loader: glob({ pattern: '**/*.{md,mdx}', base: './src/content/issues' }),
  schema: z.object({
    number: z.number(),
    title: z.string(),
    subtitle: z.string().optional(),
    cluster: z.string(),
    month: z.string(),
    published: z.date().optional(),
    illustration: z.string().optional(),
    status: z.enum(['scaffold', 'draft', 'published']).default('scaffold'),
  }),
});

export const collections = { issues };
