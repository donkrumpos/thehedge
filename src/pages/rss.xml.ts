import rss from '@astrojs/rss';
import { getCollection } from 'astro:content';
import type { APIContext } from 'astro';

export async function GET(context: APIContext) {
  const issues = await getCollection('issues');
  const published = issues
    .filter((i) => i.data.status === 'published')
    .sort(
      (a, b) =>
        (b.data.published?.getTime() ?? 0) - (a.data.published?.getTime() ?? 0),
    );

  return rss({
    title: 'The Hedge',
    description: 'Weekly reports from the edge of village.',
    site: context.site!,
    items: published.map((issue) => ({
      title: issue.data.title,
      description: issue.data.subtitle ?? '',
      pubDate: issue.data.published,
      link: `/issues/${issue.id}/`,
    })),
  });
}
