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

function resumePayload(page) {
  return {
    layout: document.getElementById('preview-layout').value,
    accent_color: document.getElementById('accent-color').value,
    markdown: resumeMarkdown(page),
    editorial_header: {
      eyebrow: page.querySelector('.eyebrow')?.innerText.trim() || '',
      role: page.querySelector('.role')?.innerText.trim() || '',
    },
  };
}

const layoutPicker = document.getElementById('preview-layout');
const accentPicker = document.getElementById('accent-color');
function applyAccent(accent) {
  const channels = accent.slice(1).match(/.{2}/g).map(channel => parseInt(channel, 16) / 255);
  const luminance = channels.map(channel => channel <= 0.04045 ? channel / 12.92 : ((channel + 0.055) / 1.055) ** 2.4)
    .reduce((sum, channel, index) => sum + channel * [0.2126, 0.7152, 0.0722][index], 0);
  document.body.style.setProperty('--accent', accent);
  document.body.style.setProperty('--accent-ink', luminance > 0.179 ? '#111111' : '#ffffff');
}
let customAccent;
try { customAccent = localStorage.getItem(key + '-accent'); } catch (error) { /* storage may be unavailable */ }
if (customAccent && /^#[0-9a-f]{6}$/i.test(customAccent)) {
  accentPicker.value = customAccent;
} else {
  accentPicker.value = document.body.dataset.layout === 'editorial-html' ? '#466454' : document.body.dataset.layout === 'single-column' ? '#1a1a1a' : '#2b4c5e';
}
applyAccent(accentPicker.value);
accentPicker.addEventListener('input', () => {
  applyAccent(accentPicker.value);
  try { localStorage.setItem(key + '-accent', accentPicker.value); } catch (error) { /* preview still works */ }
});
layoutPicker.value = document.body.dataset.layout;
layoutPicker.addEventListener('change', () => {
  const page = document.querySelector('.page');
  const oldLayout = page.querySelector('.layout');
  const header = page.querySelector('header');
  const contact = page.querySelector('.contact');
  const summaryLabel = page.querySelector('.summary-label');
  const intro = page.querySelector('.intro');
  const mainSections = [...oldLayout.querySelectorAll('section:not(.aside-section)')];
  const sidebarSections = [...oldLayout.querySelectorAll('section.aside-section')];
  const layout = document.createElement('div');
  const main = document.createElement('div');
  const sidebar = document.createElement('aside');
  layout.className = 'layout';
  main.className = 'main-column';
  sidebar.className = 'sidebar';
  oldLayout.before(header);
  if (layoutPicker.value === 'two-column-left') {
    header.append(contact, summaryLabel);
    sidebar.append(header, ...sidebarSections);
    main.append(intro, ...mainSections);
    layout.append(sidebar, main);
  } else if (layoutPicker.value === 'two-column-right') {
    sidebar.append(contact, ...sidebarSections);
    main.append(intro, ...mainSections);
    layout.append(main, sidebar);
  } else {
    header.append(contact, summaryLabel, intro);
    main.append(...mainSections);
    if (layoutPicker.value === 'single-column') {
      main.append(...sidebarSections);
      layout.append(main);
    } else {
      sidebar.append(...sidebarSections);
      layout.append(main, sidebar);
    }
  }
  oldLayout.replaceWith(layout);
  document.body.dataset.layout = layoutPicker.value;
  try { localStorage.setItem(key + '-layout', layoutPicker.value); } catch (error) { /* editing still works */ }
  page.dispatchEvent(new Event('input', { bubbles: true }));
});

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
      body: JSON.stringify(resumePayload(page)),
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