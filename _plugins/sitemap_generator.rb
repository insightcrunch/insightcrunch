module Jekyll
  class SitemapGenerator < Generator
    safe true
    priority :low

    URLS_PER_SITEMAP = 250

    def generate(site)
      # Collect all posts plus pages you want indexed
      all_urls = []

      site.posts.docs.each do |post|
        all_urls << {
          loc: "#{site.config['url']}#{post.url}",
          lastmod: (post.data['last_modified_at'] || post.date).strftime('%Y-%m-%dT%H:%M:%S%:z')
        }
      end

      # Optionally include static pages
      site.pages.each do |page|
        next unless page.output_ext == '.html'
        next if page.data['sitemap'] == false
        next if page.path.start_with?('404')
        all_urls << {
          loc: "#{site.config['url']}#{page.url}",
          lastmod: site.time.strftime('%Y-%m-%dT%H:%M:%S%:z')
        }
      end

      # Chunk into groups of 250
      chunks = all_urls.each_slice(URLS_PER_SITEMAP).to_a

      # Generate child sitemap files
      chunks.each_with_index do |chunk, idx|
        sitemap_number = idx + 1
        content = build_sitemap_xml(chunk)
        site.pages << create_page(site, "sitemap-#{sitemap_number}.xml", content)
      end

      # Generate sitemap-index.xml
      index_content = build_sitemap_index_xml(site, chunks.length)
      site.pages << create_page(site, "sitemap-index.xml", index_content)
    end

    private

    def build_sitemap_xml(urls)
      xml = %(<?xml version="1.0" encoding="UTF-8"?>\n)
      xml += %(<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n)
      urls.each do |u|
        xml += "  <url>\n"
        xml += "    <loc>#{u[:loc]}</loc>\n"
        xml += "    <lastmod>#{u[:lastmod]}</lastmod>\n"
        xml += "  </url>\n"
      end
      xml += "</urlset>\n"
      xml
    end

    def build_sitemap_index_xml(site, count)
      xml = %(<?xml version="1.0" encoding="UTF-8"?>\n)
      xml += %(<sitemapindex xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n)
      (1..count).each do |n|
        xml += "  <sitemap>\n"
        xml += "    <loc>#{site.config['url']}/sitemap-#{n}.xml</loc>\n"
        xml += "    <lastmod>#{site.time.strftime('%Y-%m-%dT%H:%M:%S%:z')}</lastmod>\n"
        xml += "  </sitemap>\n"
      end
      xml += "</sitemapindex>\n"
      xml
    end

    def create_page(site, filename, content)
      page = PageWithoutAFile.new(site, site.source, '', filename)
      page.content = content
      page.data['layout'] = nil
      page.output = content
      page
    end
  end
end