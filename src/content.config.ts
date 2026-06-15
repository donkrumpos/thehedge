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

// Automated daily/weekly dispatches — grounded in real weather + phenology +
// almanac data, written by an LLM. EXPERIMENTAL automation test (2026-06-15).
const dispatches = defineCollection({
  loader: glob({ pattern: '**/*.md', base: './src/content/dispatches' }),
  schema: z.object({
    title: z.string(),
    date: z.date(),
    weather: z.string().optional(),
    generated: z.boolean().default(false),
    model: z.string().optional(),
  }),
});

export const collections = { issues, dispatches };
