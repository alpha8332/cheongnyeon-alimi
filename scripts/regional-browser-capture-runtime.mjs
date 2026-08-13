const clean = (value) => String(value ?? "").replace(/\s+/g, " ").trim();

export async function collectQueryPage({
  tab,
  endpoint,
  token,
  sourceId,
  listUrl,
  page,
  paginationValue = page,
  idParam,
  pageParam,
  pageStep = 1,
  titleSelector,
  closestSelector = null,
  linkSelector = "a",
  identityPattern = null,
  identityAttribute = null,
  listReadySelector = null,
  detailUrlTemplate = null,
  detailTitleSelector = null,
  detailContentSelector = null,
  detailPost = null,
  detailClickTemplate = null,
  detailReadySelector = null,
  titleSuffixPattern = null,
  titlePrefixPattern = null,
  applicationEndPattern = null,
  closedTextPattern = null,
  asOfDate = null,
  totalCount = null,
  hasNext: declaredHasNext,
  sourceScopeSelectors = null,
  recapture = false,
  recaptureIds = null,
}) {
  const listRequestStartedAt = Date.now();
  await tab.goto(listUrl);
  if (listReadySelector) {
    await tab.playwright.locator(listReadySelector).first().waitFor({
      state: "visible",
      timeoutMs: 20000,
    });
  }
  const audit = await tab.playwright.evaluate(
    ({ idParam: identity, pageParam: pagination, page: current, pageStep: step, titleSelector: title, closestSelector: closest, linkSelector: selectedLinks, identityPattern: identityRegex, identityAttribute: identityAttr, sourceScopeSelectors: scopeSelectors }) => {
      const squash = (value) => String(value ?? "").replace(/\s+/g, " ").trim();
      const allLinks = Array.from(document.querySelectorAll("a"));
      const links = Array.from(document.querySelectorAll(selectedLinks)).map((element) => ({
        href: element.href || location.href,
        identityValue: identityAttr ? element.getAttribute(identityAttr) : element.href,
        text: squash(element.textContent),
        listText: squash((closest ? element.closest(closest) : element)?.textContent),
        title: squash((closest ? element.closest(closest) : element)?.querySelector(title)?.textContent),
      }));
      return {
        links: links.filter((link) => {
          try {
            return identityRegex
              ? new RegExp(identityRegex).test(link.identityValue ?? "")
              : new URL(link.href, location.href).searchParams.has(identity);
          } catch {
            return false;
          }
        }),
        hasNext: allLinks.some((anchor) => {
          try {
            return Number(new URL(anchor.href, location.href).searchParams.get(pagination)) === current + step;
          } catch {
            return false;
          }
        }),
        sourceScope: scopeSelectors
          ? Object.fromEntries(
            Object.entries(scopeSelectors).map(([field, selector]) => [
              field,
              squash(document.querySelector(selector)?.textContent),
            ]),
          )
          : null,
      };
    },
    { idParam, pageParam, page: paginationValue, pageStep, titleSelector, closestSelector, linkSelector, identityPattern, identityAttribute, sourceScopeSelectors },
  );
  const discovered = [];
  const seen = new Set();
  for (const link of audit.links) {
    const externalId = identityPattern
      ? String(link.identityValue ?? "").match(new RegExp(identityPattern))?.[1]
      : new URL(link.href).searchParams.get(idParam);
    if (!externalId || seen.has(externalId)) continue;
    seen.add(externalId);
    discovered.push({
      external_id: externalId,
      detail_url: detailUrlTemplate
        ? detailUrlTemplate.replace("{id}", externalId)
        : link.href,
      title: clean(link.title || link.text)
        .replace(titlePrefixPattern ? new RegExp(titlePrefixPattern) : /$^/, "")
        .replace(titleSuffixPattern ? new RegExp(titleSuffixPattern) : /$^/, "")
        .trim(),
      list_text: clean(link.listText || link.text),
    });
  }
  if (recaptureIds !== null) {
    if (
      !recapture
      || !Array.isArray(recaptureIds)
      || !recaptureIds.length
      || recaptureIds.length !== new Set(recaptureIds).size
    ) {
      throw new Error("limited recapture identities are invalid");
    }
    const selectedIds = new Set(recaptureIds.map(String));
    const selected = discovered.filter((item) => selectedIds.has(item.external_id));
    if (selected.length !== selectedIds.size) {
      throw new Error("limited recapture identity is absent from official list");
    }
    discovered.splice(0, discovered.length, ...selected);
  }
  if (!discovered.length) throw new Error(`no identities on ${listUrl}`);
  const hasNext = declaredHasNext ?? audit.hasNext;
  const pending = recapture
    ? new Set(discovered.map((item) => item.external_id))
    : new Set((await postDiscovery(endpoint, token, {
      source_id: sourceId,
      page,
      total_count: totalCount,
      has_next: hasNext,
      discovered_ids: discovered.map((item) => item.external_id),
    })).pending_ids);
  const listClosed = [];
  if (closedTextPattern || (applicationEndPattern && asOfDate)) {
    const closedPattern = closedTextPattern ? new RegExp(closedTextPattern) : null;
    const endPattern = applicationEndPattern ? new RegExp(applicationEndPattern) : null;
    for (const item of discovered) {
      const closedMatch = closedPattern ? item.list_text.match(closedPattern) : null;
      const match = endPattern ? item.list_text.match(endPattern) : null;
      const normalizedEnd = match?.[1]?.replace(/[.\/]/g, "-");
      const isClosed = Boolean(closedMatch) || Boolean(
        normalizedEnd && asOfDate && normalizedEnd < asOfDate,
      );
      if (isClosed && pending.has(item.external_id)) {
        listClosed.push({
          ...item,
          application_period: closedMatch?.[0] || match[0],
        });
      }
    }
  }
  for (let start = 0; start < listClosed.length; start += 3) {
    const items = listClosed.slice(start, start + 3).map((item) => ({
      external_id: item.external_id,
      title: item.title,
      summary: null,
      category: null,
      detail_url: item.detail_url,
      request_identity: null,
      detail: {
        title: item.title,
        organization: null,
        category: null,
        application_period: item.application_period,
        source_region: null,
        eligibility: null,
        support_content: null,
        application_method: null,
        contact: null,
        required_documents: null,
        exclusions: null,
        age: null,
      },
    }));
    await postCapture(endpoint, token, {
      source_id: sourceId,
      source_scope: audit.sourceScope,
      list_url: listUrl,
      page,
      total_count: totalCount,
      has_next: hasNext,
      discovered_ids: discovered.map((item) => item.external_id),
      action_trace: [
        "goto approved list",
        `paginate page ${page}`,
        "classify closed from official list period",
      ],
      items,
    });
  }
  const listClosedIds = new Set(listClosed.map((item) => item.external_id));
  const pendingItems = discovered.filter(
    (item) => pending.has(item.external_id) && !listClosedIds.has(item.external_id),
  );
  for (let start = 0; start < pendingItems.length; start += 3) {
    const items = [];
    for (const item of pendingItems.slice(start, start + 3)) {
      let detail;
      const requestStartedAt = Date.now();
      try {
        if (detailPost) {
          await tab.goto(listUrl);
          if (!detailClickTemplate) throw new Error("detail POST click selector missing");
          await tab.playwright
            .locator(detailClickTemplate.replace("{id}", item.external_id))
            .first()
            .click();
          if (detailReadySelector) {
            await tab.playwright.locator(detailReadySelector).first().waitFor({
              state: "visible",
              timeoutMs: 20000,
            });
          }
        } else {
          await tab.goto(item.detail_url);
        }
        if (!detail) detail = await extractDetail(
          tab,
          item.title,
          detailTitleSelector,
          detailContentSelector,
        );
      } catch (error) {
        if (recapture) throw error;
        await postFailure(endpoint, token, {
          source_id: sourceId,
          page,
          total_count: totalCount,
          has_next: hasNext,
          discovered_ids: discovered.map((value) => value.external_id),
          failed_id: item.external_id,
          reason: String(error.message).slice(0, 300),
        });
        continue;
      } finally {
        const remainingInterval = Math.max(0, 2000 - (Date.now() - requestStartedAt));
        if (remainingInterval) await tab.playwright.waitForTimeout(remainingInterval);
      }
      items.push({
        external_id: item.external_id,
        title: detail.title,
        summary: null,
        category: detail.category,
        detail_url: item.detail_url,
        request_identity: detailPost
          ? [
            `${detailPost.identityField}=${item.external_id}`,
            ...Object.entries(detailPost.fields).map(
              ([key, value]) => `${key}=${value}`,
            ),
          ].join("&")
          : null,
        detail,
      });
    }
    if (items.length) await postCapture(endpoint, token, {
      source_id: sourceId,
      source_scope: audit.sourceScope,
      list_url: listUrl,
      page,
      total_count: totalCount,
      has_next: hasNext,
      discovered_ids: discovered.map((item) => item.external_id),
      action_trace: [
        "goto approved list",
        "apply approved scope filter",
        `paginate page ${page}`,
        recapture ? "recapture selected detail" : "observe detail batch",
      ],
      items,
    });
  }
  const remainingListInterval = Math.max(
    0,
    2000 - (Date.now() - listRequestStartedAt),
  );
  if (remainingListInterval) await tab.playwright.waitForTimeout(remainingListInterval);
  return {
    page,
    count: discovered.length,
    pending: pendingItems.length,
    listClosed: listClosed.length,
    hasNext,
  };
}

async function postDiscovery(endpoint, token, discovery) {
  const response = await fetch(endpoint.replace(/\/capture$/, "/discover"), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Connection: "close",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(discovery),
  });
  const body = await response.json();
  if (!response.ok || !Array.isArray(body.pending_ids)) {
    throw new Error(JSON.stringify(body));
  }
  return body;
}

async function postFailure(endpoint, token, failure) {
  const response = await fetch(endpoint.replace(/\/capture$/, "/failure"), {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Connection: "close",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(failure),
  });
  const body = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(body));
  return body;
}

export async function extractDetail(
  tab,
  expectedTitle,
  detailTitleSelector,
  detailContentSelector,
) {
  const extracted = await tab.playwright.evaluate(({titleSelector, contentSelector}) => {
    const squash = (value) => String(value ?? "").replace(/\s+/g, " ").trim();
    const compact = (value) => squash(value).replace(/\s/g, "");
    const pairs = {};
    for (const element of document.querySelectorAll("dt,th,strong")) {
      const key = squash(element.textContent).replace(/[:：]\s*$/, "");
      let value = squash(element.nextElementSibling?.textContent);
      if (!value && element.tagName === "STRONG") {
        const chunks = [];
        for (let sibling = element.nextSibling; sibling; sibling = sibling.nextSibling) {
          if (sibling.nodeType === Node.ELEMENT_NODE && sibling.tagName === "STRONG") break;
          chunks.push(sibling.textContent ?? "");
        }
        value = squash(chunks.join(" "));
      }
      if (key && !(key in pairs)) pairs[key] = value;
    }
    for (const element of document.querySelectorAll("h3,h4")) {
      const key = squash(element.textContent).replace(/[:：]\s*$/, "");
      const value = squash(element.nextElementSibling?.textContent);
      if (key && value && !(key in pairs)) pairs[key] = value;
    }
    const contentRoot = contentSelector
      ? document.querySelector(contentSelector)
      : null;
    return {
      body: compact(document.body?.innerText || document.body?.textContent),
      pairs,
      contentBlocks: contentRoot
        ? Array.from(contentRoot.querySelectorAll("p"))
          .map((element) => squash(element.textContent))
          .filter(Boolean)
        : [],
      actualTitle: titleSelector
        ? squash(document.querySelector(titleSelector)?.textContent)
        : null,
    };
  }, {titleSelector: detailTitleSelector, contentSelector: detailContentSelector});
  const actualTitle = extracted.actualTitle || expectedTitle;
  if (detailTitleSelector) {
    const expectedPrefix = clean(expectedTitle).replace(/\.{2,}\s*$/, "");
    if (!actualTitle || (expectedPrefix && !actualTitle.startsWith(expectedPrefix))) {
      throw new Error("detail title does not match truncated list title");
    }
  }
  return buildDetail(actualTitle, extracted);
}

function pairsWithProseLabels(pairs, contentBlocks = []) {
  const selected = {...pairs};
  const labelPattern = /^[\u200B\uFEFF\s]*(?:[□■▪●○]\s*)?(지원대상|신청대상|대상|자격|지원조건|지원내용|지원규모|사업내용|정책내용|주요내용|혜택|지원기간|신청기간|접수기간|모집기간|신청방법|접수방법|신청링크|접수처)\s*(?::|：)?\s*(.*)$/;
  for (let index = 0; index < contentBlocks.length; index += 1) {
    const block = clean(contentBlocks[index]);
    const match = block.match(labelPattern);
    if (!match) continue;
    const [, label, inlineValue] = match;
    const chunks = inlineValue ? [inlineValue] : [];
    if (!inlineValue) {
      for (let next = index + 1; next < contentBlocks.length; next += 1) {
        const nextBlock = clean(contentBlocks[next]);
        if (labelPattern.test(nextBlock)) break;
        if (nextBlock) chunks.push(nextBlock);
      }
    }
    if (!(label in selected)) selected[label] = clean(chunks.join(" "));
  }
  return selected;
}

export function buildDetail(title, extracted) {
  const compact = (value) => clean(value).replace(/\s/g, "");
  const expectedFull = compact(title);
  const expectedCore = expectedFull.replace(/[\(\[][\s\S]*?[\)\]]/g, "");
  if (!extracted.body.includes(expectedFull) && (!expectedCore || !extracted.body.includes(expectedCore))) {
    throw new Error("detail title does not match list");
  }
  const pairs = pairsWithProseLabels(
    extracted.pairs,
    extracted.contentBlocks,
  );
  const observations = {};
  const normalizedPairs = Object.entries(pairs).map(([key, value]) => ({
    key,
    normalizedKey: clean(key).replace(/\s/g, ""),
    value,
  }));
  const find = (field, labels) => {
    const match = labels
      .map((label) => normalizedPairs.find(({normalizedKey}) => normalizedKey === label))
      .find(Boolean);
    const value = clean(match?.value) || null;
    observations[field] = {
      label: match?.key ?? null,
      status: match
        ? (value ? "value_extracted" : "label_present_value_empty")
        : "label_not_found",
    };
    return value;
  };
  const combine = (field, labels) => {
    const matches = labels
      .map((label) => normalizedPairs.find(({normalizedKey}) => normalizedKey === label))
      .filter(Boolean);
    const values = matches.map(({value}) => clean(value)).filter(Boolean);
    const value = values.length ? [...new Set(values)].join(" ") : null;
    observations[field] = {
      label: matches.length ? matches.map(({key}) => key).join(" + ") : null,
      status: matches.length
        ? (value ? "value_extracted" : "label_present_value_empty")
        : "label_not_found",
    };
    return value;
  };
  const fromMarker = (value, pattern) => {
    const match = value?.match(pattern);
    return match?.index === undefined ? value : clean(value.slice(match.index));
  };
  const detail = {
    title,
    organization: find("organization", ["기관명", "담당기관명", "주관기관", "운영기관", "담당기관", "시행기관"]),
    category: find("category", ["정책유형", "분야", "유형", "카테고리"]),
    application_period: find("application_period", ["사업신청기간", "신청기간", "접수기간", "모집기간", "모집일시"]),
    source_region: find("source_region", ["해당지역", "사업지역", "지역", "거주지"]),
    eligibility: combine("eligibility", ["지원대상", "신청대상", "참여요건", "지원조건", "추가단서사항", "대상", "자격"]),
    support_content: find("support_content", ["지원내용", "사업내용", "정책내용", "주요내용", "혜택", "지원규모"]),
    application_method: fromMarker(
      find("application_method", ["신청방법", "접수방법", "신청링크", "공고상세보기URL", "접수처", "신청절차"]),
      /신청방법\s*[:：]?/,
    ),
    contact: find("contact", ["문의처", "문의", "담당자", "연락처"]),
    required_documents: find("required_documents", ["필요서류", "제출서류", "구비서류", "첨부파일"]),
    exclusions: find("exclusions", ["참여제한대상", "지원제외", "제외", "제한"]),
    age: find("age", ["지원연령", "연령제한", "연령", "나이"]),
  };
  return {...detail, evidence_observations: observations};
}

async function postCapture(endpoint, token, capture) {
  const response = await fetch(endpoint, {
    method: "POST",
    headers: {
      Authorization: `Bearer ${token}`,
      Connection: "close",
      "Content-Type": "application/json",
    },
    body: JSON.stringify(capture),
  });
  const body = await response.json();
  if (!response.ok) throw new Error(JSON.stringify(body));
  return body;
}

export function daeguConfig(page) {
  return {
    sourceId: "regional-daegu-youth-platform",
    listUrl: `https://www.dgjump.com/open_content/info/info_list_01?search_flag=1&page=${page}`,
    page,
    idParam: "ap_seq",
    pageParam: "page",
    titleSelector: ".tit",
    detailContentSelector: ".view_txt",
    sourceScopeSelectors: {
      jurisdiction_text: "h1",
      operator_text: "h1",
      youth_policy_scope_text: 'nav a[href="/open_content/info/info_list_01"]',
      application_scope_text: ".page-title",
    },
  };
}

export function gwangjuConfig(page) {
  return {
    sourceId: "regional-gwangju-integrated-youth-platform",
    listUrl: `https://youth.jeonnam-gwangju.go.kr/www/50?siteId=www&status=ing&pageIndex=${page}&url=%2Fwww%2Fpolicy%2FgjYgPolicyList`,
    page,
    idParam: "policyId",
    pageParam: "pageIndex",
    titleSelector: ".tit b",
    closestSelector: ".item",
    linkSelector: 'a[onclick^="policyView("]',
    identityPattern: "policyView\\('([0-9]+)'\\)",
    identityAttribute: "onclick",
    listReadySelector: 'a[onclick^="policyView("]',
    detailUrlTemplate: "https://youth.jeonnam-gwangju.go.kr/www/50?policyId={id}",
    detailTitleSelector: ".dt-tit",
    detailPost: {identityField: "policyId", fields: {}},
    detailClickTemplate: 'a[onclick="policyView(\'{id}\')"]',
    detailReadySelector: ".dt-tit",
    sourceScopeSelectors: {
      jurisdiction_text: "h1",
      operator_text: "h1",
      youth_policy_scope_text: ".sub-title h2",
      application_scope_text: ".state-ing",
    },
  };
}

export function incheonConfig(page) {
  return {
    sourceId: "regional-incheon-youth-platform",
    listUrl: `https://youth.incheon.go.kr/youthpolicy/youthPolicyInfoList.do?acptrun=ing&pgno=${page}`,
    page,
    idParam: "poly_seq",
    pageParam: "pgno",
    titleSelector: ".con-box .tit",
    closestSelector: ".boardList > li",
    linkSelector: 'a[href*="youthPolicyInfoDetail.do"][href*="poly_seq="]',
    detailTitleSelector: "#con-tit h3",
    sourceScopeSelectors: {
      jurisdiction_text: "h1",
      operator_text: "h1",
      youth_policy_scope_text: "#con-tit h3",
      application_scope_text: '#search-select2 option[selected="selected"]',
    },
  };
}

export function jeonbukConfig(page) {
  const offset = (page - 1) * 12;
  return {
    sourceId: "regional-jeonbuk-youth-platform",
    listUrl: `https://www.jb2030.or.kr/policy/p2_pol.html?offset=${offset}&strstate=ing&strbunya=&strarea=&strtarget=&strage=`,
    page,
    paginationValue: offset,
    pageStep: 12,
    idParam: "id",
    pageParam: "offset",
    titleSelector: ".list_cont .tit",
    linkSelector: 'a[href*="p2_pol_view.html"][href*="id="]',
    detailTitleSelector: ".v_tit",
    sourceScopeSelectors: {
      jurisdiction_text: "footer p",
      operator_text: "footer p",
      youth_policy_scope_text: "h1",
      application_scope_text: 'select[name="dateCheck"] option:checked',
    },
  };
}
