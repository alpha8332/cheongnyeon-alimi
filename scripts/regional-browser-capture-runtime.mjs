const clean = (value) => String(value ?? "").replace(/\s+/g, " ").trim();
const isTimeoutError = (error) => /timeout|timed out|deadline exceeded/i.test(
  String(error?.message ?? error),
);

export async function gotoWithReadyFallback(tab, url, readySelector) {
  try {
    await tab.goto(url);
    return false;
  } catch (error) {
    if (!readySelector || !isTimeoutError(error)) {
      throw error;
    }
    const loaded = await tab.playwright.evaluate(
      ({targetUrl, selector}) => {
        const current = new URL(location.href);
        const target = new URL(targetUrl, location.href);
        const sortedParams = (urlValue) => [...urlValue.searchParams]
          .sort(([leftKey, leftValue], [rightKey, rightValue]) => (
            leftKey.localeCompare(rightKey) || leftValue.localeCompare(rightValue)
          ));
        const sameTarget = current.origin === target.origin
          && current.pathname === target.pathname
          && JSON.stringify(sortedParams(current))
            === JSON.stringify(sortedParams(target));
        return sameTarget && Boolean(document.querySelector(selector));
      },
      {targetUrl: url, selector: readySelector},
    );
    if (!loaded) throw error;
    return true;
  }
}

export async function waitForReadySelector(tab, selector, timeoutMs = 20000) {
  const startedAt = Date.now();
  while (Date.now() - startedAt <= timeoutMs) {
    const ready = await tab.playwright.evaluate(
      (selected) => Boolean(document.querySelector(selected)),
      selector,
    );
    if (ready) return true;
    const remaining = timeoutMs - (Date.now() - startedAt);
    if (remaining <= 0) break;
    await new Promise((resolve) => setTimeout(resolve, Math.min(250, remaining)));
  }
  throw new Error(`ready selector timeout after ${timeoutMs}ms: ${selector}`);
}

export async function waitForExpectedTitle(
  tab,
  selector,
  expectedTitle,
  timeoutMs = 20000,
  contentSelector = null,
) {
  const expected = clean(expectedTitle).replace(/\.{2,}\s*$/, "");
  const startedAt = Date.now();
  let consecutiveMatches = 0;
  while (Date.now() - startedAt <= timeoutMs) {
    const observed = await tab.playwright.evaluate(
      ({titleSelector, detailSelector}) => ({
        title: String(document.querySelector(titleSelector)?.textContent || "")
          .replace(/\s+/g, " ")
          .trim(),
        content: detailSelector
          ? String(document.querySelector(detailSelector)?.textContent || "")
            .replace(/\s+/g, " ")
            .trim()
          : null,
      }),
      {titleSelector: selector, detailSelector: contentSelector},
    );
    const titleReady = observed.title
      && (!expected || observed.title.startsWith(expected));
    const contentReady = !contentSelector
      || (observed.content && (!expected || observed.content.includes(expected)));
    consecutiveMatches = titleReady && contentReady
      ? consecutiveMatches + 1
      : 0;
    if (consecutiveMatches >= 2) return observed.title;
    const remaining = timeoutMs - (Date.now() - startedAt);
    if (remaining <= 0) break;
    await new Promise((resolve) => setTimeout(resolve, Math.min(250, remaining)));
  }
  throw new Error(`detail title timeout after ${timeoutMs}ms`);
}

export async function withSingleDetailRetry(observe, enabled = false) {
  try {
    return await observe();
  } catch (error) {
    const retryable = /detail title (?:does not match list|timeout)/i.test(
      String(error?.message ?? error),
    );
    if (!enabled || !retryable) throw error;
    return observe();
  }
}

export function validateRecaptureExclusions(
  recapture,
  recaptureIds,
  recaptureExcludedIds,
) {
  if (recaptureExcludedIds === null) return null;
  if (
    !recapture
    || !Array.isArray(recaptureExcludedIds)
    || !recaptureExcludedIds.length
    || recaptureExcludedIds.length !== new Set(recaptureExcludedIds).size
    || recaptureExcludedIds.some((value) => typeof value !== "string" || !value)
    || Array.isArray(recaptureIds)
    && recaptureIds.some((value) => recaptureExcludedIds.includes(value))
  ) {
    throw new Error("recapture excluded identities are invalid");
  }
  return recaptureExcludedIds;
}

export function validateCheckpointDetailRecaptureContracts(
  sourceId,
  listUrl,
  items,
) {
  let approvedList;
  try {
    approvedList = new URL(listUrl);
  } catch {
    throw new Error("checkpoint detail recapture contract is invalid");
  }
  const validDaeguList = sourceId === "regional-daegu-youth-platform"
    && approvedList.origin === "https://www.dgjump.com"
    && approvedList.pathname === "/open_content/info/info_list_01"
    && approvedList.searchParams.get("search_flag") === "1";
  const validGwangjuList = sourceId
    === "regional-gwangju-integrated-youth-platform"
    && approvedList.origin === "https://youth.jeonnam-gwangju.go.kr"
    && approvedList.pathname === "/www/50"
    && approvedList.searchParams.get("siteId") === "www"
    && approvedList.searchParams.get("status") === "ing"
    && approvedList.searchParams.get("pageIndex") === "1"
    && approvedList.searchParams.get("url")
      === "/www/policy/gjYgPolicyList";
  const validIncheonList = sourceId === "regional-incheon-youth-platform"
    && approvedList.origin === "https://youth.incheon.go.kr"
    && approvedList.pathname === "/youthpolicy/youthPolicyInfoList.do"
    && approvedList.searchParams.get("acptrun") === "ing"
    && approvedList.searchParams.get("pgno") === "1";
  const validDaejeonList = sourceId === "regional-daejeon-youth-platform"
    && approvedList.origin === "https://www.daejeonyouthportal.kr"
    && approvedList.pathname === "/biz/integratedYouth.do"
    && approvedList.searchParams.get("section") === "1"
    && approvedList.searchParams.get("pageIndex") === "1";
  const validJeonbukList = sourceId === "regional-jeonbuk-youth-platform"
    && approvedList.origin === "https://www.jb2030.or.kr"
    && approvedList.pathname === "/policy/p2_pol.html"
    && approvedList.searchParams.get("offset") === "0"
    && approvedList.searchParams.get("strstate") === "ing";
  const validGyeongnamList = sourceId === "regional-gyeongnam-youth-platform"
    && approvedList.origin === "https://youth.gyeongnam.go.kr"
    && approvedList.pathname === "/youth/youthPolicySearchPageNew.es"
    && approvedList.searchParams.get("mid") === "a10101020000"
    && approvedList.searchParams.get("policy_subject_office") === "0";
  const validJejuList = sourceId === "regional-jeju-youth-platform"
    && approvedList.origin === "https://jejuyouth.com"
    && approvedList.pathname === "/m/bbs/board.php"
    && approvedList.searchParams.get("bo_table") === "1_2_2_1"
    && approvedList.searchParams.get("page") === "1";
  const validUlsanList = sourceId === "regional-ulsan-youth-platform"
    && approvedList.origin === "https://www.ulsan.go.kr"
    && approvedList.pathname === "/s/ulsanyouth/bbs/list.ulsan"
    && approvedList.searchParams.get("bbsId") === "BBS_0000000000000309"
    && approvedList.searchParams.get("mId") === "008001002000000000"
    && approvedList.searchParams.get("page") === "1";
  const validList = validDaeguList || validGwangjuList || validIncheonList
    || validDaejeonList || validJeonbukList || validGyeongnamList
    || validJejuList || validUlsanList;
  const validItems = Array.isArray(items)
    && items.length >= 1
    && items.length <= 3
    && items.length === new Set(items.map((item) => item?.external_id)).size
    && items.every((item) => {
      if (
        typeof item?.external_id !== "string"
        || !item.external_id
        || typeof item.title !== "string"
        || !clean(item.title)
        || typeof item.detail_url !== "string"
      ) return false;
      try {
        const detailUrl = new URL(item.detail_url);
        if (validDaeguList) {
          return detailUrl.origin === approvedList.origin
            && detailUrl.pathname === "/open_content/info/info_list_01_view"
            && detailUrl.searchParams.get("ap_seq") === item.external_id;
        }
        if (validGwangjuList) {
          return detailUrl.origin === approvedList.origin
            && detailUrl.pathname === "/www/50"
            && detailUrl.searchParams.get("policyId") === item.external_id;
        }
        if (validIncheonList) {
          return detailUrl.origin === approvedList.origin
            && detailUrl.pathname
              === "/youthpolicy/youthPolicyInfoDetail.do"
            && detailUrl.searchParams.get("poly_seq") === item.external_id;
        }
        if (validDaejeonList) {
          return detailUrl.origin === approvedList.origin
            && detailUrl.pathname
              === `/content/${item.external_id}/cntPage.do`;
        }
        if (validJeonbukList) {
          return detailUrl.origin === approvedList.origin
            && detailUrl.pathname === "/policy/p2_pol_view.html"
            && detailUrl.searchParams.get("id") === item.external_id;
        }
        if (validJejuList) {
          return detailUrl.origin === approvedList.origin
            && detailUrl.pathname === approvedList.pathname
            && detailUrl.searchParams.get("bo_table") === "1_2_2_1"
            && detailUrl.searchParams.get("wr_id") === item.external_id;
        }
        if (validUlsanList) {
          return detailUrl.origin === approvedList.origin
            && detailUrl.pathname === "/s/ulsanyouth/bbs/view.do"
            && detailUrl.searchParams.get("bbsId")
              === "BBS_0000000000000309"
            && detailUrl.searchParams.get("mId")
              === "008001002000000000"
            && detailUrl.searchParams.get("dataId") === item.external_id;
        }
        return validGyeongnamList
          && detailUrl.origin === approvedList.origin
          && detailUrl.pathname
            === "/youth/youthPolicySearchViewNew.es"
          && detailUrl.searchParams.get("mid") === "a10101020000"
          && detailUrl.searchParams.get("policy_no") === item.external_id;
      } catch {
        return false;
      }
    });
  if (!validList || !validItems) {
    throw new Error("checkpoint detail recapture contract is invalid");
  }
  return items;
}

export function normalizeCheckpointDetailTitle(
  value,
  expectedTitle,
  prefixPattern = null,
) {
  let normalized = clean(value);
  const expected = clean(expectedTitle).replace(/\.{2,}\s*$/, "");
  const prefix = prefixPattern ? new RegExp(prefixPattern) : null;
  while (prefix && !normalized.startsWith(expected)) {
    const next = normalized.replace(prefix, "").trim();
    if (next === normalized) break;
    normalized = next;
  }
  return normalized;
}

export async function collectCheckpointDetailRecapture({
  tab,
  endpoint,
  token,
  sourceId,
  listUrl,
  items,
  detailTitleSelector,
  detailTitlePrefixPattern = null,
  detailContentSelector,
  detailPairRowSelector = null,
  detailPairLabelSelector = null,
  detailPairValueSelector = null,
  detailMetadataSelector = null,
  detailRegionSelector = null,
  sourceScopeSelectors,
  checkpointTotalCount = null,
}) {
  const contracts = validateCheckpointDetailRecaptureContracts(
    sourceId,
    listUrl,
    items,
  );
  if (!detailTitleSelector || !detailContentSelector || !sourceScopeSelectors) {
    throw new Error("checkpoint detail recapture selectors are incomplete");
  }
  const captured = [];
  let sourceScope = null;
  for (const contract of contracts) {
    const requestStartedAt = Date.now();
    try {
      await gotoWithReadyFallback(tab, contract.detail_url, detailTitleSelector);
      await waitForReadySelector(tab, detailContentSelector);
      const observed = await tab.playwright.evaluate(
        ({titleSelector, scopeSelectors}) => {
          const squash = (value) => String(value ?? "").replace(/\s+/g, " ").trim();
          return {
            title: squash(document.querySelector(titleSelector)?.textContent),
            sourceScope: Object.fromEntries(
              Object.entries(scopeSelectors).map(([field, selector]) => [
                field,
                squash(document.querySelector(selector)?.textContent),
              ]),
            ),
          };
        },
        {titleSelector: detailTitleSelector, scopeSelectors: sourceScopeSelectors},
      );
      const actualTitle = normalizeCheckpointDetailTitle(
        observed.title,
        contract.title,
        detailTitlePrefixPattern,
      );
      const expectedTitle = clean(contract.title).replace(/\.{2,}\s*$/, "");
      if (!actualTitle || !actualTitle.startsWith(expectedTitle)) {
        throw new Error("checkpoint detail title does not match frozen Raw");
      }
      sourceScope ??= observed.sourceScope;
      const detail = await extractDetail(
        tab,
        actualTitle,
        null,
        detailContentSelector,
        detailPairRowSelector,
        detailPairLabelSelector,
        detailPairValueSelector,
        detailMetadataSelector,
        detailRegionSelector,
      );
      captured.push({
        external_id: contract.external_id,
        title: actualTitle,
        summary: null,
        category: detail.category,
        detail_url: contract.detail_url,
        request_identity: null,
        detail,
      });
    } finally {
      const remainingInterval = Math.max(0, 2000 - (Date.now() - requestStartedAt));
      if (remainingInterval) await tab.playwright.waitForTimeout(remainingInterval);
    }
  }
  await postCapture(endpoint, token, {
    source_id: sourceId,
    recapture_mode: "checkpoint_detail_url",
    source_scope: sourceScope,
    list_url: listUrl,
    page: 1,
    total_count: checkpointTotalCount,
    has_next: false,
    discovered_ids: contracts.map((item) => item.external_id),
    action_trace: [
      "load frozen checkpoint Raw identity contract",
      "goto approved historical detail URL",
      "verify current detail title against frozen Raw",
      "recapture checkpoint detail fields",
    ],
    items: captured,
  }, "recapture");
  return {count: captured.length, ids: captured.map((item) => item.external_id)};
}

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
  listPageLinkNavigation = false,
  detailUrlTemplate = null,
  detailTitleSelector = null,
  detailContentSelector = null,
  detailPairRowSelector = null,
  detailPairLabelSelector = null,
  detailPairValueSelector = null,
  detailMetadataSelector = null,
  detailRegionSelector = null,
  detailDateInference = null,
  detailPost = null,
  detailClickTemplate = null,
  detailReadySelector = null,
  detailFromListContext = false,
  detailRetryOnMismatch = false,
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
  recaptureExcludedIds = null,
  recover = false,
  recoverIds = null,
}) {
  const listRequestStartedAt = Date.now();
  const prepareListPage = async () => {
    const readySelector = listReadySelector || linkSelector;
    await gotoWithReadyFallback(tab, listUrl, readySelector);
    if (page !== 1 && listPageLinkNavigation) {
      const pageGroup = Math.floor((page - 1) / 10);
      for (let group = 0; group < pageGroup; group += 1) {
        await tab.playwright.getByRole(
          "link",
          {name: "10페이지 뒤로 이동", exact: true},
        ).click();
      }
      if ((page - 1) % 10 !== 0) {
        await tab.playwright.getByRole(
          "link",
          {name: String(page), exact: true},
        ).click();
      }
    }
    if (readySelector) {
      await waitForReadySelector(tab, readySelector);
    }
  };
  await prepareListPage();
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
  if (recapture && recover) {
    throw new Error("recapture and failed recovery are mutually exclusive");
  }
  const selectedRecoveryIds = recover ? recoverIds : recapture ? recaptureIds : null;
  validateRecaptureExclusions(recapture, recaptureIds, recaptureExcludedIds);
  if (selectedRecoveryIds !== null) {
    if (
      !(recapture || recover)
      || !Array.isArray(selectedRecoveryIds)
      || !selectedRecoveryIds.length
      || selectedRecoveryIds.length !== new Set(selectedRecoveryIds).size
    ) {
      throw new Error("limited capture identities are invalid");
    }
    const selectedIds = new Set(selectedRecoveryIds.map(String));
    const selected = discovered.filter((item) => selectedIds.has(item.external_id));
    if (selected.length !== selectedIds.size) {
      throw new Error("limited capture identity is absent from official list");
    }
    discovered.splice(0, discovered.length, ...selected);
  }
  if (!discovered.length) throw new Error(`no identities on ${listUrl}`);
  const hasNext = declaredHasNext ?? audit.hasNext;
  const pending = recapture || recover
    ? new Set(discovered.map((item) => item.external_id))
    : new Set((await postDiscovery(endpoint, token, {
      source_id: sourceId,
      page,
      total_count: totalCount,
      has_next: hasNext,
      discovered_ids: discovered.map((item) => item.external_id),
    })).pending_ids);
  const listClosed = [];
  if (!recover && (closedTextPattern || (applicationEndPattern && asOfDate))) {
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
        detail = await withSingleDetailRetry(async () => {
          if (detailPost) {
            await prepareListPage();
            if (!detailClickTemplate) throw new Error("detail POST click selector missing");
            await tab.playwright
              .locator(detailClickTemplate.replace("{id}", item.external_id))
              .first()
              .click();
            if (detailReadySelector) {
              await waitForReadySelector(tab, detailReadySelector);
            }
          } else {
            if (detailFromListContext) await prepareListPage();
            await gotoWithReadyFallback(
              tab,
              item.detail_url,
              detailContentSelector || detailTitleSelector,
            );
          }
          if (detailTitleSelector) {
            await waitForExpectedTitle(
              tab,
              detailTitleSelector,
              item.title,
              20000,
              detailContentSelector,
            );
          }
          return extractDetail(
            tab,
            item.title,
            detailTitleSelector,
            detailContentSelector,
            detailPairRowSelector,
            detailPairLabelSelector,
            detailPairValueSelector,
            detailMetadataSelector,
            detailRegionSelector,
            detailDateInference,
            asOfDate,
          );
        }, detailRetryOnMismatch);
      } catch (error) {
        if (recapture || recover) throw error;
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
      ...(recaptureExcludedIds === null
        ? {}
        : {recapture_excluded_ids: recaptureExcludedIds}),
      action_trace: [
        "goto approved list",
        "apply approved scope filter",
        `paginate page ${page}`,
        recover
          ? "recover selected failed detail"
          : recapture
            ? "recapture selected detail"
            : "observe detail batch",
      ],
      items,
    }, recover ? "recover" : recapture ? "recapture" : "capture");
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
  detailPairRowSelector = null,
  detailPairLabelSelector = null,
  detailPairValueSelector = null,
  detailMetadataSelector = null,
  detailRegionSelector = null,
  detailDateInference = null,
  detailAsOfDate = null,
) {
  const extracted = await tab.playwright.evaluate(({
    titleSelector,
    contentSelector,
    pairRowSelector,
    pairLabelSelector,
    pairValueSelector,
    metadataSelector,
    regionSelector,
  }) => {
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
    if (!pairRowSelector) {
      for (const element of document.querySelectorAll("h3,h4")) {
        const key = squash(element.textContent).replace(/[:：]\s*$/, "");
        const chunks = [];
        for (
          let sibling = element.nextElementSibling;
          sibling;
          sibling = sibling.nextElementSibling
        ) {
          if (sibling.matches("h3,h4")) break;
          const value = squash(sibling.textContent);
          if (value) chunks.push(value);
        }
        const value = squash(chunks.join(" "));
        if (key && value && !(key in pairs)) pairs[key] = value;
      }
    }
    if (pairRowSelector && pairLabelSelector && pairValueSelector) {
      for (const row of document.querySelectorAll(pairRowSelector)) {
        const key = squash(row.querySelector(pairLabelSelector)?.textContent)
          .replace(/[:：]\s*$/, "");
        const value = squash(row.querySelector(pairValueSelector)?.textContent);
        if (key && !(key in pairs)) pairs[key] = value;
      }
    }
    const contentRoot = contentSelector
      ? document.querySelector(contentSelector)
      : null;
    const contentBlocks = [];
    if (contentRoot) {
      for (const element of contentRoot.querySelectorAll("p")) {
        const value = squash(element.textContent);
        if (value && !contentBlocks.includes(value)) contentBlocks.push(value);
      }
      for (const line of String(contentRoot.innerText ?? "").split(/\n+/)) {
        const value = squash(line);
        if (value && !contentBlocks.includes(value)) contentBlocks.push(value);
      }
    }
    return {
      body: compact(document.body?.innerText || document.body?.textContent),
      pairs,
      contentBlocks,
      actualTitle: titleSelector
        ? squash(document.querySelector(titleSelector)?.textContent)
        : null,
      metadataText: metadataSelector
        ? squash(document.querySelector(metadataSelector)?.textContent)
        : null,
      sourceRegionText: regionSelector
        ? squash(document.querySelector(regionSelector)?.textContent)
        : null,
    };
  }, {
    titleSelector: detailTitleSelector,
    contentSelector: detailContentSelector,
    pairRowSelector: detailPairRowSelector,
    pairLabelSelector: detailPairLabelSelector,
    pairValueSelector: detailPairValueSelector,
    metadataSelector: detailMetadataSelector,
    regionSelector: detailRegionSelector,
  });
  const actualTitle = extracted.actualTitle || expectedTitle;
  if (detailTitleSelector) {
    const cleanedExpected = clean(expectedTitle).replace(/\.{2,}\s*$/, "");
    const replacementPrefix = cleanedExpected.split("�", 1)[0].trim();
    const expectedPrefix = replacementPrefix.length >= 8
      ? replacementPrefix
      : cleanedExpected;
    if (!actualTitle || (expectedPrefix && !actualTitle.startsWith(expectedPrefix))) {
      throw new Error("detail title does not match truncated list title");
    }
  }
  const detail = detailDateInference === "registered_title_deadline"
    ? buildRegisteredTitleDeadlineDetail(actualTitle, extracted, detailAsOfDate)
    : buildDetail(actualTitle, extracted);
  if (detailRegionSelector) {
    detail.source_region = clean(extracted.sourceRegionText) || null;
    detail.evidence_observations.source_region = {
      label: detailRegionSelector,
      status: detail.source_region
        ? "value_extracted"
        : "label_present_value_empty",
    };
  }
  return detail;
}

export function buildRegisteredTitleDeadlineDetail(
  title,
  extracted,
  asOfDate,
) {
  const detail = buildDetail(title, extracted);
  if (detail.application_period) return detail;
  const registered = clean(extracted.metadataText).match(
    /등록일\s*:\s*(\d{4})[.\/-](\d{1,2})[.\/-](\d{1,2})/,
  );
  const deadline = clean(title).match(
    /\(~\s*(\d{1,2})[.\/-](\d{1,2})[.]?(?:\s*(\d{1,2}:\d{2}))?\s*\)/,
  );
  if (!registered || !deadline) return detail;
  if (!/^\d{4}-\d{2}-\d{2}$/.test(asOfDate || "")) {
    throw new Error("dated title inference requires an as-of date");
  }
  const year = registered[1];
  const [, month, day, time] = deadline;
  const registeredIso = `${year}-${registered[2].padStart(2, "0")}-${registered[3].padStart(2, "0")}`;
  const deadlineIso = `${year}-${month.padStart(2, "0")}-${day.padStart(2, "0")}`;
  if (deadlineIso < registeredIso) return detail;
  const value = [
    deadlineIso,
    time || null,
    deadlineIso < asOfDate ? "마감" : null,
    `(상세 등록일 ${registeredIso})`,
  ].filter(Boolean).join(" ");
  return {
    ...detail,
    application_period: value,
    evidence_observations: {
      ...detail.evidence_observations,
      application_period: {
        label: "제목 기한 + 등록일",
        status: "value_extracted",
      },
    },
  };
}

function pairsWithProseLabels(pairs, contentBlocks = []) {
  const selected = {...pairs};
  const labelPattern = /^[^가-힣A-Za-z0-9]*(?:(?:\d+|[가-힣])[.)]\s*)?(지원대상|신청대상|모집대상|참여자격|대상|자격|지원조건|거주지|지원내용|지원규모|사업내용|정책내용|주요내용|혜택|지원기간|운영기간|운영일정|신청기간|접수기간|접수일정|모집기간|제출기한|신청방법|접수방법|신청링크|접수처|제외대상|문의처)\s*(?::|：)?\s*(.*)$/;
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
    category: find("category", ["정책유형", "정책분야", "분야", "유형", "카테고리"]),
    application_period: combine("application_period", ["접수일정", "사업신청기간", "신청기간", "접수기간", "모집기간", "모집일시", "신청기한", "제출기한"]),
    source_region: find("source_region", ["해당지역", "사업지역", "지역", "거주지"]),
    eligibility: combine("eligibility", ["지원대상", "신청대상", "모집대상", "신청자격", "참여자격", "참여요건", "지원조건", "거주지및소득", "거주지", "추가단서사항", "대상", "자격"]),
    support_content: find("support_content", ["지원내용", "사업내용", "정책내용", "주요내용", "혜택", "지원규모"]),
    application_method: fromMarker(
      find("application_method", ["신청방법", "접수방법", "신청링크", "공고상세보기URL", "접수처", "신청절차"]),
      /신청방법\s*[:：]?/,
    ),
    contact: find("contact", ["문의처", "문의", "담당자", "연락처"]),
    required_documents: find("required_documents", ["필요서류", "제출서류", "구비서류", "첨부파일"]),
    exclusions: find("exclusions", ["참여제한대상", "참여제한사항", "제외대상", "지원제외", "제외", "제한"]),
    age: find("age", ["지원연령", "연령제한", "연령", "나이"]),
  };
  const titleOrganization = clean(title).match(/^\s*[([]([^\])]+)[\])]/)?.[1];
  if (
    !detail.organization
    && titleOrganization
    && /(울산|광역시|특별시|특별자치도|도청|시청|구청|군청|센터|복지관|진흥원|공단|재단|부|청|원)$/.test(titleOrganization)
  ) {
    detail.organization = titleOrganization;
    observations.organization = {
      label: "상세 제목 기관 접두어",
      status: "value_extracted",
    };
  }
  const operationPeriod = normalizedPairs.find(
    ({normalizedKey}) => normalizedKey === "운영기간",
  );
  if (
    detail.application_period?.includes("상시")
    && clean(operationPeriod?.value)
  ) {
    detail.application_period = `운영기간: ${clean(operationPeriod.value)}`;
    observations.application_period = {
      label: [
        observations.application_period.label,
        operationPeriod.key,
      ].filter(Boolean).join(" + "),
      status: "value_extracted",
    };
  }
  return {...detail, evidence_observations: observations};
}

async function postCapture(endpoint, token, capture, mode = "capture") {
  const baseEndpoint = endpoint.replace(
    /\/(?:capture|discover|failure|recapture|recover)\/?$/,
    "",
  );
  const response = await fetch(`${baseEndpoint}/${mode}`, {
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

export function daeguCheckpointDetailConfig() {
  return {
    ...daeguConfig(1),
    detailTitleSelector: "h4.v_tit",
    detailTitlePrefixPattern: "^\\[\\s*[^\\]]+\\]\\s*",
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
    detailRegionSelector: ".detail-policy .detail-into-top .tag .badge.type07",
    sourceScopeSelectors: {
      jurisdiction_text: "h1",
      operator_text: "h1",
      youth_policy_scope_text: ".sub-title h2",
      application_scope_text: ".state-ing",
    },
  };
}

export function buildGyeongnamApiDetail(result) {
  const decodeEntities = (input) => String(input ?? "")
    .replace(/&quot;/gi, '"')
    .replace(/&#39;|&apos;/gi, "'")
    .replace(/&lt;/gi, "<")
    .replace(/&gt;/gi, ">")
    .replace(/&middot;/gi, "·")
    .replace(/&nbsp;/gi, " ")
    .replace(/&amp;/gi, "&")
    .replace(/&#(\d+);/g, (_match, code) => String.fromCodePoint(Number(code)))
    .replace(/&#x([0-9a-f]+);/gi, (_match, code) => (
      String.fromCodePoint(Number.parseInt(code, 16))
    ));
  const value = (...names) => {
    for (const name of names) {
      const selected = clean(decodeEntities(result?.[name]));
      if (selected) return selected;
    }
    return null;
  };
  const periodParts = [
    value("policy_apply_start_date"),
    value("policy_apply_end_date"),
  ];
  const fields = {
    organization: value(
      "policy_agency_name",
      "policy_operation_office",
      "policy_subject_office_str",
    ),
    category: value("policy_type_str"),
    application_period: periodParts.every(Boolean)
      ? `${periodParts[0]} ~ ${periodParts[1]}`
      : periodParts.find(Boolean) || null,
    source_region: value("policy_area_str", "policy_location"),
    eligibility: value("policy_target_content", "policy_target_str"),
    support_content: value("policy_content", "policy_howtouse"),
    application_method: value("private_url", "policy_apply_site"),
    contact: [value("policy_agency_name"), value("policy_agency_tel")]
      .filter(Boolean).join(" ") || null,
    required_documents: value("policy_document"),
    exclusions: value("policy_restrict"),
    age: value("policy_age_str") || (
      value("begin_age") && value("end_age")
        ? `${value("begin_age")} ~ ${value("end_age")}`
        : null
    ),
  };
  const labels = {
    organization: "policy_agency_name|policy_operation_office|policy_subject_office_str",
    category: "policy_type_str",
    application_period: "policy_apply_start_date|policy_apply_end_date",
    source_region: "policy_area_str|policy_location",
    eligibility: "policy_target_content|policy_target_str",
    support_content: "policy_content|policy_howtouse",
    application_method: "private_url|policy_apply_site",
    contact: "policy_agency_name|policy_agency_tel",
    required_documents: "policy_document",
    exclusions: "policy_restrict",
    age: "policy_age_str|begin_age|end_age",
  };
  return {
    title: value("policy_title"),
    ...fields,
    evidence_observations: Object.fromEntries(
      Object.entries(fields).map(([field, fieldValue]) => [
        field,
        {
          status: fieldValue ? "value_extracted" : "label_not_found",
          label: fieldValue ? labels[field] : null,
        },
      ]),
    ),
  };
}

export async function collectGyeongnamApiCheckpointRecapture({
  endpoint,
  token,
  listUrl,
  items,
  checkpointTotalCount,
  requestJson = async (url) => {
    const response = await fetch(url, {headers: {Accept: "application/json"}});
    if (!response.ok) throw new Error(`Gyeongnam API HTTP ${response.status}`);
    return response.json();
  },
}) {
  const sourceId = "regional-gyeongnam-youth-platform";
  const contracts = validateCheckpointDetailRecaptureContracts(
    sourceId,
    listUrl,
    items,
  );
  const captured = [];
  for (const contract of contracts) {
    const startedAt = Date.now();
    try {
      const apiUrl = new URL(
        "/youth/youthPolicyInfoNew.es",
        "https://youth.gyeongnam.go.kr",
      );
      apiUrl.searchParams.set("policy_no", contract.external_id);
      const payload = await requestJson(apiUrl.toString());
      if (payload?.apiResponse?.status !== 200) {
        throw new Error("Gyeongnam API response is unsuccessful");
      }
      const detail = buildGyeongnamApiDetail(payload.result);
      if (
        String(payload?.result?.policy_no) !== contract.external_id
        || !detail.title
        || !detail.title.startsWith(clean(contract.title))
      ) {
        throw new Error("Gyeongnam API identity does not match frozen Raw");
      }
      captured.push({
        external_id: contract.external_id,
        title: detail.title,
        summary: null,
        category: detail.category,
        detail_url: contract.detail_url,
        request_identity: `GET ${apiUrl.pathname}?policy_no=${contract.external_id}`,
        detail,
      });
    } finally {
      const remaining = Math.max(0, 2000 - (Date.now() - startedAt));
      if (remaining) await new Promise((resolve) => setTimeout(resolve, remaining));
    }
  }
  await postCapture(endpoint, token, {
    source_id: sourceId,
    recapture_mode: "checkpoint_detail_url",
    source_scope: {
      jurisdiction_text: "경상남도",
      operator_text: "경상남도 청년정보플랫폼",
      youth_policy_scope_text: "경남 청년정책",
      application_scope_text: "공식 정책 상세 API 신청기간·신청방법 필드",
    },
    list_url: listUrl,
    page: 1,
    total_count: checkpointTotalCount,
    has_next: false,
    discovered_ids: contracts.map((item) => item.external_id),
    action_trace: [
      "load frozen checkpoint Raw identity contract",
      "GET official policy detail JSON endpoint",
      "verify policy_no and title against frozen Raw",
      "recapture review detail fields",
    ],
    items: captured,
  }, "recapture");
  return {count: captured.length, ids: captured.map((item) => item.external_id)};
}

export function gwangjuCheckpointDetailConfig() {
  return {
    ...gwangjuConfig(1),
    detailContentSelector: ".detail-policy",
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

export function incheonCheckpointDetailConfig() {
  const config = incheonConfig(1);
  return {
    ...config,
    detailContentSelector: "#contents",
    sourceScopeSelectors: {
      ...config.sourceScopeSelectors,
      application_scope_text: "#contents",
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

export function jeonbukCheckpointDetailConfig() {
  const config = jeonbukConfig(1);
  return {
    ...config,
    detailContentSelector: ".board_view",
    sourceScopeSelectors: {
      ...config.sourceScopeSelectors,
      application_scope_text: ".board_view",
    },
  };
}

export function chungbukConfig(page) {
  return {
    sourceId: "regional-chungbuk-youth-platform",
    listUrl: `https://www.chungbuk.go.kr/young/selectBbsNttList.do?key=1283&bbsNo=174&pageIndex=${page}`,
    page,
    idParam: "nttNo",
    pageParam: "pageIndex",
    titleSelector: ".p-subject span",
    closestSelector: "tr",
    linkSelector: '.p-subject a[href*="selectBbsNttView.do"][href*="nttNo="]',
    detailContentSelector: ".p-table__content",
  };
}

export function ulsanConfig(page) {
  return {
    sourceId: "regional-ulsan-youth-platform",
    listUrl: `https://www.ulsan.go.kr/s/ulsanyouth/bbs/list.ulsan?bbsId=BBS_0000000000000309&mId=008001002000000000&page=${page}`,
    page,
    idParam: "dataId",
    pageParam: "page",
    titleSelector: ".tit",
    closestSelector: "li",
    linkSelector: '.bodo_list a[href*="view.do"][href*="dataId="]',
    detailTitleSelector: ".title_here",
    detailContentSelector: "#board_normal_view",
    detailReadySelector: ".title_here",
    detailFromListContext: true,
    detailRetryOnMismatch: true,
    titlePrefixPattern: "^(?:접수(?:전|중|마감|일정\\s*없음)|마감)\\s*",
  };
}

export function seoulConfig(page) {
  if (!Number.isInteger(page) || page < 1 || page > 23) {
    throw new Error("Seoul page is outside the observed 1..23 range");
  }
  const cityPage = page <= 18;
  const localPage = cityPage ? page : page - 18;
  const listPath = cityPage ? "ctList.do" : "guList.do";
  const tabQuery = cityPage ? "tabKind=002" : "tab=002&tabKind=003";
  return {
    sourceId: "regional-seoul-youth-platform",
    listUrl: `https://youth.seoul.go.kr/infoData/plcyInfo/${listPath}?key=2309150002&pageIndex=${localPage}&orderBy=regYmd%20desc&blueWorksYn=N&${tabQuery}`,
    page,
    paginationValue: localPage,
    idParam: "plcyBizId",
    pageParam: "pageIndex",
    titleSelector: ".tit.txt-over1",
    linkSelector: 'a.tit[onclick^="goView("]',
    listReadySelector: 'a.tit[onclick^="goView("]',
    identityPattern: "goView\\('([^']+)'\\)",
    identityAttribute: "onclick",
    detailUrlTemplate: "https://youth.seoul.go.kr/infoData/plcyInfo/view.do?key=2309150002&plcyBizId={id}",
    detailTitleSelector: ".policy-detail strong.title",
    detailContentSelector: ".policy-detail",
    detailReadySelector: ".policy-detail .form-table",
  };
}

export function daejeonConfig(page) {
  return {
    sourceId: "regional-daejeon-youth-platform",
    listUrl: `https://www.daejeonyouthportal.kr/biz/integratedYouth.do?section=1&commonMenuNo=438_323_514_517&pageIndex=${page}`,
    page,
    idParam: "identity-path",
    pageParam: "pageIndex",
    titleSelector: ".cont_tit",
    closestSelector: "li",
    linkSelector: '.bd_thum.type_biz > li > a[href*="/content/CT_"]',
    identityPattern: "/content/(CT_[^/]+)/cntPage\\.do",
    identityAttribute: "href",
  };
}

export function gangwonConfig(page) {
  if (!Number.isInteger(page) || page < 1 || page > 29) {
    throw new Error("Gangwon page is outside the observed 1..29 range");
  }
  return {
    sourceId: "regional-gangwon-youth-platform",
    listUrl: "https://job.gwd.go.kr/youth/policies/search/gangwon_policies",
    page,
    idParam: "data-id",
    pageParam: "pageIndex",
    titleSelector: "a.tit.detail",
    closestSelector: ".result-card-box",
    linkSelector: "a.tit.detail[data-id]",
    listReadySelector: "a.tit.detail[data-id]",
    listPageLinkNavigation: true,
    identityPattern: "^(.+)$",
    identityAttribute: "data-id",
    detailPost: {identityField: "bizId", fields: {mode: "gw"}},
    detailClickTemplate: 'a.tit.detail[data-id="{id}"]',
    detailReadySelector: ".skinTb-data-resList",
    detailPairRowSelector: ".skinTb-tr",
    detailPairLabelSelector: ".skinTb-th",
    detailPairValueSelector: ".skinTb-td",
  };
}

export function buildGangwonCanaryPlan(checkpoint, cycle = 0) {
  if (
    checkpoint?.source_id !== "regional-gangwon-youth-platform"
    || !Array.isArray(checkpoint.discovered_ids)
    || !Array.isArray(checkpoint.decisions)
    || !Number.isInteger(cycle)
    || cycle < 0
  ) {
    throw new Error("Gangwon canary checkpoint input is invalid");
  }
  const outcomes = new Map(
    checkpoint.decisions.map((item) => [String(item.external_id), item.outcome]),
  );
  const byPage = new Map();
  checkpoint.discovered_ids.forEach((externalId, index) => {
    if (outcomes.get(String(externalId)) !== "failed") return;
    const page = Math.floor(index / 12) + 1;
    if (!byPage.has(page)) byPage.set(page, []);
    byPage.get(page).push(String(externalId));
  });
  const strata = [
    {name: "early", firstPage: 2, lastPage: 10},
    {name: "middle", firstPage: 11, lastPage: 20},
    {name: "late", firstPage: 21, lastPage: 29},
  ];
  const canaries = strata.map((stratum) => {
    const pages = [];
    for (let page = stratum.firstPage; page <= stratum.lastPage; page += 1) {
      if (byPage.get(page)?.length) pages.push(page);
    }
    if (!pages.length) throw new Error("Gangwon canary stratum has no failed identity");
    const page = pages[cycle % pages.length];
    const identities = byPage.get(page);
    return {
      stratum: stratum.name,
      page,
      external_id: identities[cycle % identities.length],
    };
  });
  return {
    schema_version: "1.0.0",
    source_id: checkpoint.source_id,
    cycle,
    failed_count: [...outcomes.values()].filter((value) => value === "failed").length,
    canaries,
  };
}

export function classifyDetailCanaryObservation(observation) {
  if (!observation?.identity_present) return "page_or_identity_changed";
  if (observation.deleted_or_private) return "deleted_or_private";
  if (!observation.navigation_completed) return "detail_click_or_post_contract";
  if (!observation.ready_visible) return "dynamic_render_wait";
  if (!observation.title_matches) return "page_or_identity_changed";
  if (!Number.isInteger(observation.field_row_count) || observation.field_row_count < 1) {
    return "response_success_without_field_dom";
  }
  return "healthy";
}

export async function probeGangwonDetailCanary({
  tab,
  page,
  externalId,
  expectedTitle = null,
}) {
  const config = gangwonConfig(page);
  await tab.goto(config.listUrl);
  const pageGroup = Math.floor((page - 1) / 10);
  for (let group = 0; group < pageGroup; group += 1) {
    await tab.playwright.getByRole(
      "link",
      {name: "10페이지 뒤로 이동", exact: true},
    ).click();
  }
  if ((page - 1) % 10 !== 0) {
    await tab.playwright.getByRole(
      "link",
      {name: String(page), exact: true},
    ).click();
  }
  await tab.playwright.locator(config.listReadySelector).first().waitFor({
    state: "visible",
    timeoutMs: 20000,
  });
  const selector = config.detailClickTemplate.replace("{id}", externalId);
  const listTitle = await tab.playwright.evaluate(
    (selected) => String(document.querySelector(selected)?.textContent || "")
      .replace(/\s+/g, " ")
      .trim(),
    selector,
  );
  const identityPresent = Boolean(listTitle);
  const observation = {
    page,
    external_id: externalId,
    list_title: listTitle || null,
    identity_present: identityPresent,
    navigation_completed: false,
    ready_visible: false,
    title_matches: false,
    field_row_count: 0,
    deleted_or_private: false,
  };
  if (!identityPresent) {
    return {...observation, classification: classifyDetailCanaryObservation(observation)};
  }
  try {
    await tab.playwright.locator(selector).first().click();
    observation.navigation_completed = true;
  } catch {
    return {...observation, classification: classifyDetailCanaryObservation(observation)};
  }
  try {
    await tab.playwright.locator(config.detailReadySelector).first().waitFor({
      state: "visible",
      timeoutMs: 20000,
    });
    observation.ready_visible = true;
  } catch {
    const bodyText = await tab.playwright.evaluate(
      () => String(document.body?.innerText || "").replace(/\s+/g, " ").trim(),
    );
    observation.deleted_or_private = /삭제|비공개|접근 권한|존재하지 않/.test(bodyText);
    return {...observation, classification: classifyDetailCanaryObservation(observation)};
  }
  const detailState = await tab.playwright.evaluate(() => ({
    fieldRowCount: document.querySelectorAll(".skinTb-tr").length,
    bodyText: String(document.body?.innerText || "").replace(/\s+/g, " ").trim(),
  }));
  observation.field_row_count = detailState.fieldRowCount;
  observation.deleted_or_private = /삭제|비공개|접근 권한|존재하지 않/.test(
    detailState.bodyText,
  );
  const titleCandidate = clean(expectedTitle || listTitle).replace(/\.{2,}\s*$/, "");
  const replacementPrefix = titleCandidate.split("�", 1)[0].trim();
  const titlePrefix = replacementPrefix.length >= 8
    ? replacementPrefix
    : titleCandidate;
  observation.title_matches = Boolean(
    titlePrefix && detailState.bodyText.includes(titlePrefix),
  );
  return {...observation, classification: classifyDetailCanaryObservation(observation)};
}

export function jejuConfig(page, asOfDate) {
  if (!Number.isInteger(page) || page < 1 || page > 200) {
    throw new Error("Jeju page is outside the approved pagination range");
  }
  if (!/^\d{4}-\d{2}-\d{2}$/.test(asOfDate || "")) {
    throw new Error("Jeju recovery requires an as-of date");
  }
  return {
    sourceId: "regional-jeju-youth-platform",
    listUrl: `https://jejuyouth.com/m/bbs/board.php?bo_table=1_2_2_1&page=${page}`,
    page,
    asOfDate,
    idParam: "wr_id",
    pageParam: "page",
    titleSelector: "a",
    closestSelector: "li",
    linkSelector: 'a[href*="bo_table=1_2_2_1"][href*="wr_id="]',
    detailTitleSelector: ".view_title",
    detailContentSelector: "#writeContents",
    detailMetadataSelector: ".mb_area",
    detailDateInference: "registered_title_deadline",
    closedTextPattern: "모집마감",
  };
}

export function ulsanCheckpointDetailConfig() {
  const config = ulsanConfig(1);
  return {
    ...config,
    sourceScopeSelectors: {
      jurisdiction_text: "header",
      operator_text: "header",
      youth_policy_scope_text: "h1",
      application_scope_text: "#board_normal_view",
    },
  };
}

export function jejuCheckpointDetailConfig(asOfDate) {
  const config = jejuConfig(1, asOfDate);
  return {
    ...config,
    sourceScopeSelectors: {
      jurisdiction_text: ".view_title",
      operator_text: ".mb_area",
      youth_policy_scope_text: ".view_title",
      application_scope_text: ".mb_area",
    },
  };
}

export function daejeonCheckpointDetailConfig() {
  const config = daejeonConfig(1);
  return {
    ...config,
    detailTitleSelector: "h3",
    detailContentSelector: "#txt",
    sourceScopeSelectors: {
      jurisdiction_text: "h1",
      operator_text: "h1",
      youth_policy_scope_text: "h3",
      application_scope_text: "#txt",
    },
  };
}
