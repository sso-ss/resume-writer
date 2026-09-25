function resumeMarkdown(page) {
  const text = element => element?.innerText.trim() || '';
  const inline = element => {
    const clone = element.cloneNode(true);
    for (const bold of clone.querySelectorAll('strong, b')) bold.replaceWith(`**${bold.textContent}**`);
    for (const line of clone.querySelectorAll('br')) line.replaceWith('\n');
    return clone.textContent.trim();
  };
  const lines = [
    `# ${text(page.querySelector('h1'))}`, '',
    [...page.querySelector('.contact').children].map(text).join(' | '), '',
    '## Summary', '', text(page.querySelector('.intro')), '',
  ];
  for (const section of page.querySelectorAll('.layout section')) {
    const sectionName = section.dataset.section || text(section.querySelector('h2'));
    const type = {
      experience: 'Experience', 'selected projects': 'Selected Projects',
      expertise: 'Expertise', tools: 'Tools', recognition: 'Recognition', education: 'Education',
    }[sectionName.toLowerCase()] || sectionName;
    if (type === 'Experience') {
      lines.push('## Experience', '');
      for (const job of section.querySelectorAll('.job')) {
        const title = job.querySelector('h3').cloneNode(true);
        const company = text(job.querySelector('.org'));
        title.querySelector('.org')?.remove();
        lines.push(`### ${title.textContent.trim().replace(/\s*\|\s*$/, '')} | ${company} | ${text(job.querySelector('.meta'))}`);
        for (const bullet of job.querySelectorAll('li')) lines.push(`- ${inline(bullet)}`);
        lines.push('');
      }
    } else if (type === 'Selected Projects') {
      lines.push('## Key Projects', '');
      for (const project of section.querySelectorAll('.project')) {
        lines.push(`- **${text(project.querySelector('h3'))}** - ${[...project.querySelectorAll('p')].map(inline).join(' ')}`);
      }
    } else if (type === 'Expertise' || type === 'Tools') {
      if (type === 'Expertise') lines.push('## Skills & Tools', '');
      for (const paragraph of section.querySelectorAll('p')) {
        const clone = paragraph.cloneNode(true);
        const label = clone.querySelector('.label');
        const name = label?.textContent.trim() || 'Tools';
        label?.remove();
        lines.push(`- **${name.replace(/:$/, '')}:** ${clone.textContent.trim()}`);
      }
    } else {
      lines.push(`## ${type}`, '');
      for (const paragraph of section.querySelectorAll('p')) {
        lines.push(`${type === 'Recognition' ? '- ' : ''}${inline(paragraph)}`);
      }
    }
    lines.push('');
  }
  return lines.join('\n');
}

async function exportResume(event, format) {
  const button = event.currentTarget;
  const label = format === 'pdf' ? 'PDF' : 'Word';
  const token = document.querySelector('meta[name="word-export-token"]')?.content;
  if (!token) {
    alert('Export needs the local Python preview server. Ask the resume agent to open this resume with serve_resume.py. Your edits remain in this page.');
    return;
  }
  button.disabled = true;
  button.textContent = `Generating ${label}...`;
  try {
    const page = document.querySelector('.page');
    const response = await fetch(`/export-${format}`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json', 'X-Resume-Token': token },
      body: JSON.stringify({
        markdown: resumeMarkdown(page),
        editorial_header: {
          eyebrow: page.querySelector('.eyebrow')?.innerText.trim() || '',
          role: page.querySelector('.role')?.innerText.trim() || '',
        },
      }),
    });
    if (!response.ok) throw new Error(await response.text());
    const url = URL.createObjectURL(await response.blob());
    const link = document.createElement('a');
    link.href = url;
    const name = page.querySelector('h1').textContent.trim().replace(/[^a-z0-9_-]+/gi, '_');
    link.download = `${name || 'ProductDesigner'}_Resume.${format === 'pdf' ? 'pdf' : 'docx'}`;
    document.body.append(link);
    link.click();
    link.remove();
    setTimeout(() => URL.revokeObjectURL(url), 60000);
  } catch (error) {
    console.error(error);
    alert(`${label} export failed. Keep the local preview server running and try again. Your browser edits are unchanged.`);
  } finally {
    button.disabled = false;
    button.textContent = `Save as ${label}`;
  }
}

document.getElementById('save-word').addEventListener('click', event => exportResume(event, 'word'));
document.getElementById('save-pdf').addEventListener('click', event => exportResume(event, 'pdf'));