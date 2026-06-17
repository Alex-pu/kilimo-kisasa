const nativeApiBase =
  window.Capacitor?.isNativePlatform?.() ? "http://10.0.2.2:8000" : null;
const deployedApiBase = import.meta.env.VITE_API_BASE_URL || null;
const API_BASE =
  localStorage.getItem("kisasaApiBase") || deployedApiBase || nativeApiBase || "http://127.0.0.1:8000";

const state = {
  activeIssue: null,
  expandedIssueId: null,
  expandedTab: null,
  agrovets: [],
  adminApplications: [],
  adminLogin: false,
  managedAgrovets: [],
  commentsByIssue: {},
  authMode: "login",
  filter: "all",
  issues: [],
  jackLocation: null,
  jackMessages: [
    {
      role: "assistant",
      content: "Jack: Ask me a farm question, or tag @Jack in a comment and I will reply under that post.",
    },
  ],
  jackKnowledge: [],
  myAgrovet: null,
  myCatalogue: [],
  myApplications: [],
  products: [],
  productAgrovetId: null,
  recommendationsByIssue: {},
  replyingCommentId: null,
  route: window.location.pathname === "/admin" ? "#admin" : window.location.hash || "#feed",
  search: "",
  shopSearch: "",
  token: localStorage.getItem("kisasaToken"),
  user: null,
};

const els = {
  agrovetCount: document.querySelector("#agrovetCount"),
  agrovetList: document.querySelector("#agrovetList"),
  agrovetExploreList: document.querySelector("#agrovetExploreList"),
  agrovetSearch: document.querySelector("#agrovetSearch"),
  adminApplicationsCard: document.querySelector("#adminApplicationsCard"),
  adminApplicationList: document.querySelector("#adminApplicationList"),
  adminAddAgrovetButton: document.querySelector("#adminAddAgrovetButton"),
  adminAgrovetList: document.querySelector("#adminAgrovetList"),
  adminAgrovetsPanel: document.querySelector("#adminAgrovetsPanel"),
  adminLoginButton: document.querySelector("#adminLoginButton"),
  adminJackKnowledgeList: document.querySelector("#adminJackKnowledgeList"),
  adminJackKnowledgePanel: document.querySelector("#adminJackKnowledgePanel"),
  adminPage: document.querySelector("#adminPage"),
  adminPageApplicationList: document.querySelector("#adminPageApplicationList"),
  adminPanel: document.querySelector("#adminPanel"),
  agrovetForm: document.querySelector("#agrovetForm"),
  agrovetLatitude: document.querySelector("#agrovetLatitude"),
  agrovetLongitude: document.querySelector("#agrovetLongitude"),
  agrovetModal: document.querySelector("#agrovetModal"),
  agrovetRegisterCard: document.querySelector("#agrovetRegisterCard"),
  authButton: document.querySelector("#authButton"),
  authForm: document.querySelector("#authForm"),
  authModal: document.querySelector("#authModal"),
  authSubmit: document.querySelector("#authSubmit"),
  authTitle: document.querySelector("#authTitle"),
  bottomAskButton: document.querySelector("#bottomAskButton"),
  bottomAuthButton: document.querySelector("#bottomAuthButton"),
  composer: document.querySelector(".composer"),
  expertApplicationForm: document.querySelector("#expertApplicationForm"),
  expertApplicationModal: document.querySelector("#expertApplicationModal"),
  expertApplyCard: document.querySelector("#expertApplyCard"),
  feedList: document.querySelector("#feedList"),
  feedTabs: document.querySelector(".feed-tabs"),
  agrovetsPage: document.querySelector("#agrovetsPage"),
  issueCount: document.querySelector("#issueCount"),
  issueForm: document.querySelector("#issueForm"),
  issueImage: document.querySelector("#issueImage"),
  issueImagePreview: document.querySelector("#issueImagePreview"),
  issueModal: document.querySelector("#issueModal"),
  issueModalTitle: document.querySelector("#issueModalTitle"),
  jackChatForm: document.querySelector("#jackChatForm"),
  jackContext: document.querySelector("#jackContext"),
  jackKnowledgeContent: document.querySelector("#jackKnowledgeContent"),
  jackKnowledgeFilename: document.querySelector("#jackKnowledgeFilename"),
  jackKnowledgeForm: document.querySelector("#jackKnowledgeForm"),
  jackMessages: document.querySelector("#jackMessages"),
  jackPage: document.querySelector("#jackPage"),
  jackPrompt: document.querySelector("#jackPrompt"),
  menuButton: document.querySelector("#menuButton"),
  mobileSearch: document.querySelector("#mobileSearch"),
  myCatalogueCard: document.querySelector("#myCatalogueCard"),
  myCatalogueList: document.querySelector("#myCatalogueList"),
  myApplicationList: document.querySelector("#myApplicationList"),
  nameField: document.querySelector("#nameField"),
  openIssueModal: document.querySelector("#openIssueModal"),
  openExpertApplication: document.querySelector("#openExpertApplication"),
  openAgrovetRegistration: document.querySelector("#openAgrovetRegistration"),
  openProductModal: document.querySelector("#openProductModal"),
  postTypeField: document.querySelector("#postTypeField"),
  postTypeSelect: document.querySelector("#postTypeSelect"),
  productCount: document.querySelector("#productCount"),
  productForm: document.querySelector("#productForm"),
  productModal: document.querySelector("#productModal"),
  productList: document.querySelector("#productList"),
  sideAskButton: document.querySelector("#sideAskButton"),
  statusStrip: document.querySelector("#statusStrip"),
  startSellingButton: document.querySelector("#startSellingButton"),
  toggleAuthMode: document.querySelector("#toggleAuthMode"),
  useDeviceLocation: document.querySelector("#useDeviceLocation"),
  verifyField: document.querySelector("#verifyField"),
};

function authHeaders() {
  return state.token ? { Authorization: `Bearer ${state.token}` } : {};
}

async function api(path, options = {}) {
  const isFormData = options.body instanceof FormData;
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      ...authHeaders(),
      ...(options.headers || {}),
    },
  });

  if (!response.ok) {
    let message = `Request failed (${response.status})`;
    try {
      const body = await response.json();
      message = Array.isArray(body.detail)
        ? body.detail.map(item => item.msg).join(", ")
        : body.detail || message;
    } catch {
      // Keep fallback message.
    }
    throw new Error(message);
  }

  return response.status === 204 ? null : response.json();
}

function showStatus(message, tone = "info") {
  els.statusStrip.hidden = false;
  els.statusStrip.textContent = message;
  els.statusStrip.dataset.tone = tone;
}

function clearStatus() {
  els.statusStrip.hidden = true;
  els.statusStrip.textContent = "";
}

function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;");
}

function readableCategory(category) {
  return String(category || "other").replaceAll("_", " ");
}

function formatDate(value) {
  if (!value) return "now";
  return new Intl.DateTimeFormat("en", {
    day: "numeric",
    month: "short",
  }).format(new Date(value));
}

function mediaUrl(url) {
  if (!url) return "";
  return url.startsWith("http") ? url : `${API_BASE}${url}`;
}

function canAddRecommendation() {
  return ["expert", "admin"].includes(state.user?.role);
}

function canCreateExpertPost() {
  return ["expert", "admin"].includes(state.user?.role);
}

function isAdmin() {
  return state.user?.role === "admin";
}

function canApplyForExpert() {
  return Boolean(state.user) && !["expert", "admin"].includes(state.user.role);
}

function readablePostType(postType) {
  const labels = {
    issue: "issue",
    educational: "education",
    farming_news: "farming news",
  };
  return labels[postType] || "issue";
}

async function loadCurrentUser() {
  if (!state.token) {
    state.user = null;
    return null;
  }

  try {
    state.user = await api("/api/v1/users/me");
    return state.user;
  } catch {
    state.user = null;
    state.token = null;
    localStorage.removeItem("kisasaToken");
    return null;
  }
}

async function loadExpertApplications() {
  state.myApplications = [];
  state.adminApplications = [];

  if (!state.user) return;

  if (canApplyForExpert()) {
    state.myApplications = await api("/api/v1/expert-applications/me");
  }

  if (isAdmin()) {
    state.adminApplications = await api("/api/v1/expert-applications/?status=pending");
  }
}

async function loadJackKnowledge() {
  state.jackKnowledge = [];
  if (!isAdmin()) return;
  state.jackKnowledge = await api("/api/v1/jack/knowledge");
}

async function loadMyAgrovet() {
  state.myAgrovet = null;
  state.myCatalogue = [];
  state.managedAgrovets = [];

  if (!state.user) return;

  try {
    state.myAgrovet = await api("/api/v1/agrovets/me");
    state.myCatalogue = await api(`/api/v1/agrovets/${state.myAgrovet.id}/products`);
  } catch {
    state.myAgrovet = null;
    state.myCatalogue = [];
  }

  if (isAdmin()) {
    state.managedAgrovets = await api("/api/v1/agrovets/managed/");
  }
}

function filteredIssues() {
  const search = state.search.trim().toLowerCase();
  return state.issues.filter(issue => {
    const matchesFilter =
      state.filter === "all" ||
      issue.post_type === state.filter ||
      (state.filter === "urgent" && issue.is_urgent) ||
      issue.status === state.filter;
    const matchesSearch =
      !search ||
      [issue.title, issue.description, issue.category, issue.post_type, issue.location_name]
        .filter(Boolean)
        .some(value => value.toLowerCase().includes(search));
    return matchesFilter && matchesSearch;
  });
}

function renderFeed() {
  const issues = filteredIssues();
  els.feedList.innerHTML =
    issues
      .map(
        issue => `
          <article class="post-card">
            <div class="vote-column" aria-label="Post score">
              <button class="vote-arrow ${issue.my_vote === 1 ? "active" : ""}" type="button" aria-label="Upvote" data-action="vote" data-vote-value="1" data-issue-id="${issue.id}">▲</button>
              <span>${issue.score ?? 0}</span>
              <button class="vote-arrow ${issue.my_vote === -1 ? "active" : ""}" type="button" aria-label="Downvote" data-action="vote" data-vote-value="-1" data-issue-id="${issue.id}">▼</button>
            </div>
            <div class="post-body">
              <div class="post-meta">
                <span>c/${escapeHtml(readableCategory(issue.category))}</span>
                <span>•</span>
                <span>${escapeHtml(issue.location_name || "Kenya")}</span>
                <span>•</span>
                <span>${formatDate(issue.created_at)}</span>
                <span class="badge type-${escapeHtml(issue.post_type || "issue")}">${escapeHtml(readablePostType(issue.post_type))}</span>
                ${
                  issue.is_urgent
                    ? '<span class="badge urgent">urgent</span>'
                    : `<span class="badge">${escapeHtml(issue.status)}</span>`
                }
              </div>
              <h2 class="post-title">${escapeHtml(issue.title)}</h2>
              ${
                issue.image_urls?.[0]
                  ? `<img class="post-image" src="${escapeHtml(mediaUrl(issue.image_urls[0]))}" alt="">`
                  : ""
              }
              <p class="post-description">${escapeHtml(issue.description)}</p>
              <div class="post-actions">
                <button class="action" type="button" data-action="comments" data-issue-id="${issue.id}">Comments</button>
                <button class="action" type="button" data-action="recommendations" data-issue-id="${issue.id}">Expert recommendations</button>
                <button class="action" type="button" data-action="share" data-issue-id="${issue.id}">Share</button>
              </div>
              ${renderInlinePanel(issue)}
            </div>
          </article>
        `,
      )
      .join("") ||
    `<article class="post-card"><div class="vote-column">0</div><div class="post-body"><h2 class="post-title">No posts found</h2><p class="post-description">Try another filter or create the first issue.</p></div></article>`;
}

function filteredAgrovets() {
  const search = state.shopSearch.trim().toLowerCase();
  return state.agrovets.filter(agrovet => {
    if (!search) return true;
    return [agrovet.name, agrovet.location_name, agrovet.contact_person_name]
      .filter(Boolean)
      .some(value => value.toLowerCase().includes(search));
  });
}

function productsForAgrovet(agrovetId) {
  return state.products.filter(product => String(product.agrovet_id) === String(agrovetId));
}

function renderAgrovetsPage() {
  const shops = filteredAgrovets();
  els.agrovetExploreList.innerHTML =
    shops
      .map(agrovet => {
        const products = productsForAgrovet(agrovet.id).slice(0, 3);
        return `
          <article class="shop-card">
            <div class="shop-card-header">
              <div>
                <h2>${escapeHtml(agrovet.name)}</h2>
                <p>${escapeHtml(agrovet.location_name)}</p>
              </div>
              <span class="badge">${agrovet.verification_status ? "verified" : "listed"}</span>
            </div>
            <div class="compact-meta">
              ${escapeHtml(agrovet.contact_person_name || "Shop contact")} &middot;
              ${escapeHtml(agrovet.phone_number)} &middot;
              ${Number(agrovet.rating || 0).toFixed(1)} rating
            </div>
            <div class="catalogue-preview">
              ${
                products
                  .map(
                    product => `
                      <div class="catalogue-row">
                        <span>${escapeHtml(product.product_name)}</span>
                        <strong>${escapeHtml(product.currency)} ${Number(product.price || 0).toLocaleString("en")}</strong>
                      </div>
                    `,
                  )
                  .join("") || emptyThread("No catalogue products listed yet.")
              }
            </div>
          </article>
        `;
      })
      .join("") || emptyThread("No agrovets found.");
}

function renderJackPage() {
  els.jackMessages.innerHTML = state.jackMessages
    .map(
      message => `
        <article class="jack-message ${message.role === "user" ? "from-user" : "from-jack"}">
          <div class="thread-meta">${message.role === "user" ? "You" : "Jack"}</div>
          <p>${escapeHtml(message.content)}</p>
        </article>
      `,
    )
    .join("");
  els.jackMessages.scrollTop = els.jackMessages.scrollHeight;
}

function renderRoute() {
  const agrovetsRoute = state.route === "#agrovets";
  const adminRoute = state.route === "#admin";
  const jackRoute = state.route === "#jack";
  const nonFeedRoute = agrovetsRoute || adminRoute || jackRoute;
  els.composer.hidden = nonFeedRoute;
  els.feedTabs.hidden = nonFeedRoute;
  els.mobileSearch.closest(".mobile-search").hidden = nonFeedRoute;
  els.feedList.hidden = nonFeedRoute;
  els.agrovetsPage.hidden = !agrovetsRoute;
  els.adminPage.hidden = !adminRoute;
  els.jackPage.hidden = !jackRoute;
  document.querySelectorAll(".rail-link, .bottom-link").forEach(link => {
    const activeRoute = jackRoute ? "#jack" : agrovetsRoute ? "#agrovets" : "#feed";
    link.classList.toggle("active", link.getAttribute("href") === activeRoute);
  });
  if (agrovetsRoute) renderAgrovetsPage();
  if (adminRoute) renderAdminPage();
  if (jackRoute) renderJackPage();
}

function renderSidebars() {
  els.issueCount.textContent = state.issues.length;
  els.agrovetCount.textContent = state.agrovets.length;
  els.productCount.textContent = state.products.length;

  els.agrovetList.innerHTML = state.agrovets
    .slice(0, 5)
    .map(
      agrovet => `
        <div class="compact-item">
          <div class="compact-title">${escapeHtml(agrovet.name)}</div>
          <div class="compact-meta">${escapeHtml(agrovet.location_name)} • ${Number(agrovet.rating || 0).toFixed(1)} rating</div>
        </div>
      `,
    )
    .join("");

  els.productList.innerHTML = state.products
    .slice(0, 5)
    .map(
      product => `
        <div class="compact-item">
          <div class="compact-title">${escapeHtml(product.product_name)}</div>
          <div class="compact-meta">${escapeHtml(product.currency)} ${Number(product.price || 0).toLocaleString("en")} • ${escapeHtml(product.category)}</div>
        </div>
      `,
    )
    .join("");

  renderExpertApplicationCards();
}

function renderAdminPage() {
  els.adminLoginButton.hidden = isAdmin();
  els.adminPanel.hidden = !isAdmin();
  els.adminAgrovetsPanel.hidden = !isAdmin();
  els.adminJackKnowledgePanel.hidden = !isAdmin();

  if (!state.user) {
    els.adminPageApplicationList.innerHTML = emptyThread("Log in with an admin account.");
    els.adminAgrovetList.innerHTML = "";
    els.adminJackKnowledgeList.innerHTML = "";
    return;
  }
  if (!isAdmin()) {
    els.adminPageApplicationList.innerHTML = emptyThread("This account is not an admin.");
    els.adminAgrovetList.innerHTML = "";
    els.adminJackKnowledgeList.innerHTML = "";
    return;
  }

  els.adminPageApplicationList.innerHTML =
    state.adminApplications
      .map(
        application => `
          <div class="compact-item application-item">
            <div class="compact-title">${escapeHtml(application.applicant_name)}</div>
            <div class="compact-meta">${escapeHtml(application.applicant_email)}</div>
            <a class="compact-link" href="${escapeHtml(application.linkedin_url)}" target="_blank" rel="noreferrer">LinkedIn profile</a>
            <div class="compact-meta">${escapeHtml(application.education)}</div>
            <div class="review-actions">
              <button class="text-button" type="button" data-review-action="approved" data-application-id="${application.id}">Approve</button>
              <button class="text-button" type="button" data-review-action="rejected" data-application-id="${application.id}">Reject</button>
            </div>
          </div>
        `,
      )
      .join("") || emptyThread("No pending expert applications.");

  els.adminAgrovetList.innerHTML =
    state.managedAgrovets
      .map(
        agrovet => `
          <div class="compact-item application-item">
            <div class="compact-title">${escapeHtml(agrovet.name)}</div>
            <div class="compact-meta">${escapeHtml(agrovet.location_name)} &middot; ${escapeHtml(agrovet.contact_person_name || "Shop contact")}</div>
            <div class="compact-meta">${escapeHtml(agrovet.phone_number)}</div>
            <div class="review-actions">
              <button class="text-button" type="button" data-admin-product-agrovet="${agrovet.id}">Add product</button>
            </div>
          </div>
        `,
      )
      .join("") || emptyThread("No admin-managed agrovets yet.");

  els.adminJackKnowledgeList.innerHTML =
    state.jackKnowledge
      .map(
        document => `
          <div class="compact-item application-item">
            <div class="compact-title">${escapeHtml(document.title)}</div>
            <div class="compact-meta">${escapeHtml(document.source)}</div>
            <div class="review-actions">
              <button class="text-button" type="button" data-jack-knowledge-edit="${escapeHtml(document.source)}">Edit</button>
              <button class="text-button" type="button" data-jack-knowledge-delete="${escapeHtml(document.source)}">Delete</button>
            </div>
          </div>
        `,
      )
      .join("") || emptyThread("No Jack notes yet.");
}

function renderExpertApplicationCards() {
  els.expertApplyCard.hidden = !canApplyForExpert();
  els.adminApplicationsCard.hidden = !isAdmin();
  els.agrovetRegisterCard.hidden = !state.user || Boolean(state.myAgrovet) || state.user.role === "admin";
  els.myCatalogueCard.hidden = !state.myAgrovet;

  els.myApplicationList.innerHTML = state.myApplications
    .slice(0, 3)
    .map(
      application => `
        <div class="compact-item">
          <div class="compact-title">Application ${escapeHtml(application.status)}</div>
          <div class="compact-meta">${formatDate(application.created_at)}</div>
          ${
            application.review_notes
              ? `<div class="compact-meta">${escapeHtml(application.review_notes)}</div>`
              : ""
          }
        </div>
      `,
    )
    .join("");

  els.adminApplicationList.innerHTML =
    state.adminApplications
      .map(
        application => `
          <div class="compact-item application-item">
            <div class="compact-title">${escapeHtml(application.applicant_name)}</div>
            <div class="compact-meta">${escapeHtml(application.applicant_email)}</div>
            <a class="compact-link" href="${escapeHtml(application.linkedin_url)}" target="_blank" rel="noreferrer">LinkedIn profile</a>
            <div class="compact-meta">${escapeHtml(application.education)}</div>
            ${
              application.credentials
                ? `<div class="compact-meta">${escapeHtml(application.credentials)}</div>`
                : ""
            }
            <div class="review-actions">
              <button class="text-button" type="button" data-review-action="approved" data-application-id="${application.id}">Approve</button>
              <button class="text-button" type="button" data-review-action="rejected" data-application-id="${application.id}">Reject</button>
            </div>
          </div>
        `,
      )
      .join("") || emptyThread("No pending applications.");

  els.myCatalogueList.innerHTML =
    state.myCatalogue
      .map(
        product => `
          <div class="compact-item">
            <div class="compact-title">${escapeHtml(product.product_name)}</div>
            <div class="compact-meta">${Number(product.stock_quantity || 0).toLocaleString("en")} ${escapeHtml(product.unit || "units")} &middot; ${escapeHtml(product.currency)} ${Number(product.price || 0).toLocaleString("en")}</div>
            ${
              product.instructions
                ? `<div class="compact-meta">${escapeHtml(product.instructions)}</div>`
                : ""
            }
          </div>
        `,
      )
      .join("") || emptyThread("No catalogue products yet.");
}

function emptyThread(label) {
  return `<div class="empty-thread">${label}</div>`;
}

function buildCommentTree(comments) {
  const byId = new Map();
  const roots = [];

  comments.forEach(comment => {
    byId.set(String(comment.id), { ...comment, replies: [] });
  });

  byId.forEach(comment => {
    const parentId = comment.parent_comment_id ? String(comment.parent_comment_id) : null;
    const parent = parentId ? byId.get(parentId) : null;
    if (parent) {
      parent.replies.push(comment);
    } else {
      roots.push(comment);
    }
  });

  return roots;
}

function renderCommentNode(comment, issueId, depth = 0) {
  const isJack = String(comment.content || "").startsWith("Jack:");
  const isReplying = String(state.replyingCommentId) === String(comment.id);
  const replies = comment.replies || [];
  return `
    <article class="thread-item ${isJack ? "jack-comment" : ""}" style="--comment-depth: ${Math.min(depth, 6)}">
      <div class="thread-meta">${formatDate(comment.created_at)}</div>
      <p>${escapeHtml(comment.content)}</p>
      <div class="comment-actions">
        <button class="text-button" type="button" data-action="reply-comment" data-issue-id="${issueId}" data-comment-id="${comment.id}">Reply</button>
      </div>
      ${
        isReplying
          ? `
            <form class="reply-form nested-reply-form" data-comment-form="${issueId}" data-parent-comment-id="${comment.id}">
              <textarea name="content" rows="2" placeholder="Write a reply" required></textarea>
              <div class="reply-actions">
                <button class="primary-button" type="submit">Reply</button>
                <button class="text-button" type="button" data-action="cancel-reply" data-issue-id="${issueId}">Cancel</button>
              </div>
            </form>
          `
          : ""
      }
      ${replies.map(reply => renderCommentNode(reply, issueId, depth + 1)).join("")}
    </article>
  `;
}

function renderCommentsHtml(issueId) {
  const comments = state.commentsByIssue[issueId];
  if (!comments) return emptyThread("Loading comments...");
  const roots = buildCommentTree(comments);
  return roots.map(comment => renderCommentNode(comment, issueId)).join("") || emptyThread("No comments yet.");
}

function renderRecommendationsHtml(issueId) {
  const recommendations = state.recommendationsByIssue[issueId];
  if (!recommendations) return emptyThread("Loading expert recommendations...");
  return (
    recommendations
      .map(
        recommendation => `
          <article class="thread-item recommendation-item">
            <div class="thread-meta">${formatDate(recommendation.created_at)}</div>
            <h3>${escapeHtml(recommendation.farm_input_name)}</h3>
            <p>${escapeHtml(recommendation.rationale)}</p>
            ${
              recommendation.description
                ? `<p>${escapeHtml(recommendation.description)}</p>`
                : ""
            }
            ${
              recommendation.estimated_cost != null
                ? `<div class="thread-meta">Estimated cost: KES ${Number(recommendation.estimated_cost).toLocaleString("en")}</div>`
                : ""
            }
          </article>
        `,
      )
      .join("") || emptyThread("No expert recommendations yet.")
  );
}

function renderShareHtml(issue) {
  const url = `${window.location.origin}${window.location.pathname}#issue-${issue.id}`;
  return `
    <div class="share-row">
      <input type="text" value="${escapeHtml(url)}" readonly>
      <button class="primary-button" type="button" data-action="copy-share" data-issue-id="${issue.id}">Copy</button>
    </div>
  `;
}

function renderInlinePanel(issue) {
  if (String(state.expandedIssueId) !== String(issue.id)) return "";

  const tab = state.expandedTab || "comments";
  return `
    <section class="inline-thread" data-inline-thread="${issue.id}">
      <div class="inline-thread-header">
        <div class="inline-tabs">
          <button class="action ${tab === "comments" ? "active" : ""}" type="button" data-action="comments" data-issue-id="${issue.id}">Comments</button>
          <button class="action ${tab === "recommendations" ? "active" : ""}" type="button" data-action="recommendations" data-issue-id="${issue.id}">Expert recommendations</button>
          <button class="action ${tab === "share" ? "active" : ""}" type="button" data-action="share" data-issue-id="${issue.id}">Share</button>
        </div>
        <button class="action minimize-action" type="button" data-action="collapse" data-issue-id="${issue.id}">Minimize</button>
      </div>
      ${
        tab === "comments"
          ? `
            <div class="thread-list">${renderCommentsHtml(issue.id)}</div>
            <form class="reply-form" data-comment-form="${issue.id}">
              <textarea name="content" rows="3" placeholder="Add a comment" required></textarea>
              <button class="primary-button" type="submit">Comment</button>
            </form>
          `
          : ""
      }
      ${
        tab === "recommendations"
          ? `
            <div class="thread-list">${renderRecommendationsHtml(issue.id)}</div>
            ${
              canAddRecommendation()
                ? `
                  <form class="reply-form" data-recommendation-form="${issue.id}">
                    <input name="farm_input_name" type="text" placeholder="Recommended input or action" required>
                    <textarea name="rationale" rows="3" placeholder="Why this helps" required></textarea>
                    <textarea name="description" rows="2" placeholder="Optional details"></textarea>
                    <input name="estimated_cost" type="number" min="0" step="1" placeholder="Estimated cost">
                    <button class="primary-button" type="submit">Add recommendation</button>
                  </form>
                `
                : `<div class="role-note">Only verified experts can add expert recommendations.</div>`
            }
          `
          : ""
      }
      ${tab === "share" ? renderShareHtml(issue) : ""}
    </section>
  `;
}

async function loadInlineThreads(issueId) {
  const [comments, recommendations] = await Promise.all([
    api(`/api/v1/issues/${issueId}/comments/`),
    api(`/api/v1/issues/${issueId}/recommendations/`),
  ]);
  state.commentsByIssue[issueId] = comments;
  state.recommendationsByIssue[issueId] = recommendations;
  renderFeed();
}

async function openIssueDetail(issueId, tab = "comments") {
  const issue = state.issues.find(item => String(item.id) === String(issueId));
  if (!issue) return;

  if (String(state.expandedIssueId) === String(issueId) && state.expandedTab === tab) {
    state.expandedIssueId = null;
    state.expandedTab = null;
    state.activeIssue = null;
    state.replyingCommentId = null;
    renderFeed();
    return;
  }

  state.activeIssue = issue;
  state.expandedIssueId = issue.id;
  state.expandedTab = tab;
  state.replyingCommentId = null;
  renderFeed();

  if (tab !== "share" && (!state.commentsByIssue[issue.id] || !state.recommendationsByIssue[issue.id])) {
    try {
      await loadInlineThreads(issue.id);
    } catch (error) {
      showStatus(`Could not load post details: ${error.message}`, "error");
    }
  }
}

function shareIssue(issueId) {
  const issue = state.issues.find(item => String(item.id) === String(issueId));
  if (!issue) return;

  const url = `${window.location.origin}${window.location.pathname}#issue-${issue.id}`;
  if (navigator.share) {
    navigator.share({ title: issue.title, text: issue.description, url }).catch(() => {});
    return;
  }

  navigator.clipboard?.writeText(url);
  showStatus("Post link copied.");
}

async function handleVote(issueId, value) {
  if (!state.token) {
    setAuthMode("login");
    els.authModal.showModal();
    showStatus("Log in before voting.");
    return;
  }

  try {
    const result = await api(`/api/v1/issues/${issueId}/vote`, {
      method: "POST",
      body: JSON.stringify({ value }),
    });
    state.issues = state.issues.map(issue =>
      String(issue.id) === String(issueId)
        ? { ...issue, score: result.score, my_vote: result.my_vote }
        : issue,
    );
    renderFeed();
  } catch (error) {
    showStatus(`Could not save vote: ${error.message}`, "error");
  }
}

function renderAuth() {
  const loggedIn = Boolean(state.token);
  els.authButton.textContent = loggedIn ? "Log out" : "Log in";
  els.bottomAuthButton.textContent = loggedIn ? "Logout" : "Login";
  const expertPostAllowed = canCreateExpertPost();
  els.postTypeField.hidden = !expertPostAllowed;
  if (!expertPostAllowed) {
    els.postTypeSelect.value = "issue";
  }
  els.issueModalTitle.textContent = expertPostAllowed
    ? "Create a post"
    : "Ask the community";
}

function setAuthMode(mode) {
  state.authMode = mode;
  const signup = mode === "signup";
  els.authTitle.textContent = state.adminLogin ? "Admin login" : signup ? "Sign up" : "Log in";
  els.authSubmit.textContent = signup ? "Create account" : "Log in";
  els.toggleAuthMode.textContent = signup
    ? "Already have an account? Log in"
    : "Need an account? Sign up";
  els.nameField.hidden = state.adminLogin || !signup;
  els.verifyField.hidden = state.adminLogin || !signup;
  els.toggleAuthMode.hidden = state.adminLogin;
}

async function loadData() {
  clearStatus();
  try {
    const [issues, agrovets, products] = await Promise.all([
      api("/api/v1/issues/?limit=50"),
      api("/api/v1/agrovets/?limit=20"),
      api("/api/v1/products/?limit=30&in_stock=true"),
    ]);
    state.issues = issues;
    state.agrovets = agrovets;
    state.products = products;
    renderFeed();
    renderSidebars();
    renderRoute();
  } catch (error) {
    showStatus(`Could not load feed: ${error.message}`, "error");
  }
}

async function handleAuthSubmit(event) {
  event.preventDefault();
  const form = new FormData(els.authForm);
  const identity = String(form.get("identity") || "").trim();
  const password = String(form.get("password") || "");
  const submitLabel = els.authSubmit.textContent;

  els.authSubmit.disabled = true;
  els.authSubmit.textContent = "Signing in...";

  try {
    const endpoint =
      state.authMode === "signup"
        ? "/api/v1/auth/local-register"
        : "/api/v1/auth/local-login";
    const payload =
      state.authMode === "signup"
        ? {
            identity,
            display_name: String(form.get("display_name") || identity).trim(),
            password,
            password_verify: String(form.get("passwordVerify") || ""),
          }
        : {
            identity,
            password,
          };

    const result = await api(endpoint, {
      method: "POST",
      body: JSON.stringify(payload),
    });
    state.token = result.access_token;
    localStorage.setItem("kisasaToken", state.token);
    await loadCurrentUser();
    if (state.adminLogin && !isAdmin()) {
      state.adminLogin = false;
      await handleLogout();
      showStatus("That account is not an admin.", "error");
      return;
    }

    els.authModal.close();
    els.authForm.reset();
    state.adminLogin = false;
    renderAuth();
    renderRoute();
    showStatus(state.authMode === "signup" ? "Account created." : "Logged in.");

    try {
      await loadExpertApplications();
      await loadJackKnowledge();
      await loadMyAgrovet();
      renderSidebars();
      renderRoute();
    } catch (detailsError) {
      showStatus(`Logged in, but some admin data did not load: ${detailsError.message}`, "error");
    }
  } catch (error) {
    showStatus(error.message, "error");
  } finally {
    els.authSubmit.disabled = false;
    els.authSubmit.textContent = submitLabel;
  }
}

async function handleLogout() {
  state.token = null;
  state.user = null;
  state.myApplications = [];
  state.adminApplications = [];
  state.jackKnowledge = [];
  state.myAgrovet = null;
  state.myCatalogue = [];
  localStorage.removeItem("kisasaToken");
  state.adminLogin = false;
  renderAuth();
  renderSidebars();
  renderRoute();
  showStatus("Logged out.");
}

async function handleIssueSubmit(event) {
  event.preventDefault();
  const form = new FormData(els.issueForm);

  if (!state.token) {
    els.issueModal.close();
    setAuthMode("signup");
    els.authModal.showModal();
    showStatus("Create an account or log in before posting.");
    return;
  }

  try {
    const imageIds = [];
    const imageFile = els.issueImage.files?.[0];
    if (imageFile) {
      const uploadBody = new FormData();
      uploadBody.append("image", imageFile);
      const uploadedImage = await api("/api/v1/uploads/images", {
        method: "POST",
        body: uploadBody,
      });
      imageIds.push(uploadedImage.id);
    }

    await api("/api/v1/issues/", {
      method: "POST",
      body: JSON.stringify({
        title: String(form.get("title") || ""),
        post_type: canCreateExpertPost()
          ? String(form.get("post_type") || "issue")
          : "issue",
        category: String(form.get("category") || "other"),
        description: String(form.get("description") || ""),
        location_name: String(form.get("location_name") || ""),
        is_urgent: form.get("is_urgent") === "on",
        image_ids: imageIds,
      }),
    });
    els.issueModal.close();
    els.issueForm.reset();
    els.issueImagePreview.textContent = "";
    showStatus("Issue posted.");
    await loadData();
  } catch (error) {
    showStatus(error.message, "error");
  }
}

async function handleCommentSubmit(event) {
  event.preventDefault();
  const formElement = event.target.closest("[data-comment-form]");
  const issueId = formElement?.dataset.commentForm;
  if (!issueId) return;
  if (!state.token) {
    setAuthMode("login");
    els.authModal.showModal();
    showStatus("Log in before commenting.");
    return;
  }

  const form = new FormData(formElement);
  const parentCommentId = formElement.dataset.parentCommentId || null;
  try {
    await api(`/api/v1/issues/${issueId}/comments/`, {
      method: "POST",
      body: JSON.stringify({
        content: String(form.get("content") || ""),
        parent_comment_id: parentCommentId,
      }),
    });
    formElement.reset();
    state.replyingCommentId = null;
    delete state.commentsByIssue[issueId];
    await loadInlineThreads(issueId);
    showStatus("Comment added.");
  } catch (error) {
    showStatus(error.message, "error");
  }
}

async function getJackFarmerContext() {
  if (state.jackLocation) return state.jackLocation;
  if (!navigator.geolocation) return null;

  try {
    const position = await new Promise((resolve, reject) => {
      navigator.geolocation.getCurrentPosition(resolve, reject, {
        enableHighAccuracy: true,
        timeout: 8000,
      });
    });
    state.jackLocation = {
      location_latitude: Number(position.coords.latitude.toFixed(6)),
      location_longitude: Number(position.coords.longitude.toFixed(6)),
    };
    return state.jackLocation;
  } catch {
    return null;
  }
}

async function handleJackSubmit(event) {
  event.preventDefault();
  const prompt = els.jackPrompt.value.trim();
  if (!prompt) return;

  state.jackMessages.push({ role: "user", content: prompt });
  els.jackPrompt.value = "";
  renderJackPage();

  try {
    const farmerContext = await getJackFarmerContext();
    const result = await api("/api/v1/jack/chat", {
      method: "POST",
      body: JSON.stringify({
        prompt,
        context_text: els.jackContext.value.trim() || null,
        history: state.jackMessages.slice(-8),
        farmer_context: farmerContext,
      }),
    });
    state.jackMessages.push({ role: "assistant", content: result.reply });
    renderJackPage();
  } catch (error) {
    state.jackMessages.push({
      role: "assistant",
      content: `Jack: I could not answer right now. ${error.message}`,
    });
    renderJackPage();
  }
}

async function handleRecommendationSubmit(event) {
  event.preventDefault();
  const formElement = event.target.closest("[data-recommendation-form]");
  const issueId = formElement?.dataset.recommendationForm;
  if (!issueId) return;
  if (!state.token) {
    setAuthMode("login");
    els.authModal.showModal();
    showStatus("Log in before adding an expert recommendation.");
    return;
  }

  const form = new FormData(formElement);
  const estimatedCost = String(form.get("estimated_cost") || "").trim();
  try {
    await api(`/api/v1/issues/${issueId}/recommendations/`, {
      method: "POST",
      body: JSON.stringify({
        farm_input_name: String(form.get("farm_input_name") || ""),
        rationale: String(form.get("rationale") || ""),
        description: String(form.get("description") || "") || null,
        estimated_cost: estimatedCost ? Number(estimatedCost) : null,
      }),
    });
    formElement.reset();
    delete state.recommendationsByIssue[issueId];
    await loadInlineThreads(issueId);
    showStatus("Recommendation added.");
  } catch (error) {
    showStatus(error.message, "error");
  }
}

async function handleExpertApplicationSubmit(event) {
  event.preventDefault();
  const form = new FormData(els.expertApplicationForm);

  if (!state.token) {
    setAuthMode("login");
    els.authModal.showModal();
    showStatus("Log in before applying as an expert.");
    return;
  }

  try {
    await api("/api/v1/expert-applications/", {
      method: "POST",
      body: JSON.stringify({
        linkedin_url: String(form.get("linkedin_url") || ""),
        education: String(form.get("education") || ""),
        credentials: String(form.get("credentials") || "") || null,
        experience_summary: String(form.get("experience_summary") || "") || null,
      }),
    });
    els.expertApplicationModal.close();
    els.expertApplicationForm.reset();
    await loadExpertApplications();
    await loadJackKnowledge();
    renderSidebars();
    showStatus("Expert application submitted for admin review.");
  } catch (error) {
    showStatus(error.message, "error");
  }
}

async function reviewExpertApplication(applicationId, status) {
  try {
    await api(`/api/v1/expert-applications/${applicationId}/review`, {
      method: "PUT",
      body: JSON.stringify({
        status,
        review_notes:
          status === "approved"
            ? "Approved by admin."
            : "Rejected by admin.",
      }),
    });
    await loadExpertApplications();
    await loadJackKnowledge();
    renderSidebars();
    renderRoute();
    showStatus(status === "approved" ? "Expert approved." : "Application rejected.");
  } catch (error) {
    showStatus(error.message, "error");
  }
}

async function handleJackKnowledgeSubmit(event) {
  event.preventDefault();
  if (!isAdmin()) {
    showStatus("Log in as admin before managing Jack notes.", "error");
    return;
  }

  const form = new FormData(els.jackKnowledgeForm);
  try {
    await api("/api/v1/jack/knowledge", {
      method: "POST",
      body: JSON.stringify({
        filename: String(form.get("filename") || ""),
        content: String(form.get("content") || ""),
      }),
    });
    els.jackKnowledgeForm.reset();
    await loadJackKnowledge();
    renderRoute();
    showStatus("Jack note saved.");
  } catch (error) {
    showStatus(`Could not save Jack note: ${error.message}`, "error");
  }
}

async function editJackKnowledge(filename) {
  try {
    const document = await api(`/api/v1/jack/knowledge/${encodeURIComponent(filename)}`);
    els.jackKnowledgeFilename.value = document.source;
    els.jackKnowledgeContent.value = document.content;
    els.jackKnowledgeContent.focus();
  } catch (error) {
    showStatus(`Could not open Jack note: ${error.message}`, "error");
  }
}

async function deleteJackKnowledge(filename) {
  try {
    await api(`/api/v1/jack/knowledge/${encodeURIComponent(filename)}`, {
      method: "DELETE",
    });
    if (els.jackKnowledgeFilename.value === filename) {
      els.jackKnowledgeForm.reset();
    }
    await loadJackKnowledge();
    renderRoute();
    showStatus("Jack note deleted.");
  } catch (error) {
    showStatus(`Could not delete Jack note: ${error.message}`, "error");
  }
}

async function handleAgrovetSubmit(event) {
  event.preventDefault();
  const form = new FormData(els.agrovetForm);

  if (!state.token) {
    setAuthMode("login");
    els.authModal.showModal();
    showStatus("Log in before registering an agrovet.");
    return;
  }

  try {
    await api("/api/v1/agrovets/", {
      method: "POST",
      body: JSON.stringify({
        contact_person_name: String(form.get("contact_person_name") || ""),
        name: String(form.get("name") || ""),
        phone_number: String(form.get("phone_number") || ""),
        location_name: String(form.get("location_name") || ""),
        location_latitude: Number(form.get("location_latitude")),
        location_longitude: Number(form.get("location_longitude")),
        address: String(form.get("address") || "") || null,
      }),
    });
    els.agrovetModal.close();
    els.agrovetForm.reset();
    await loadCurrentUser();
    await loadMyAgrovet();
    renderAuth();
    renderSidebars();
    showStatus("Agrovet registered.");
  } catch (error) {
    showStatus(error.message, "error");
  }
}

async function handleProductSubmit(event) {
  event.preventDefault();
  const agrovetId = state.productAgrovetId || state.myAgrovet?.id;
  if (!agrovetId) return;

  const form = new FormData(els.productForm);
  try {
    await api(`/api/v1/agrovets/${agrovetId}/products`, {
      method: "POST",
      body: JSON.stringify({
        product_name: String(form.get("product_name") || ""),
        category: String(form.get("category") || ""),
        stock_quantity: Number(form.get("stock_quantity") || 0),
        price: Number(form.get("price") || 0),
        unit: String(form.get("unit") || "") || null,
        instructions: String(form.get("instructions") || "") || null,
      }),
    });
    els.productModal.close();
    els.productForm.reset();
    state.productAgrovetId = null;
    await loadMyAgrovet();
    await loadData();
    renderSidebars();
    renderRoute();
    showStatus("Product added to catalogue.");
  } catch (error) {
    showStatus(error.message, "error");
  }
}

function useDeviceLocation() {
  if (!navigator.geolocation) {
    showStatus("Device location is not available in this browser.", "error");
    return;
  }

  navigator.geolocation.getCurrentPosition(
    position => {
      els.agrovetLatitude.value = position.coords.latitude.toFixed(6);
      els.agrovetLongitude.value = position.coords.longitude.toFixed(6);
      showStatus("Location added.");
    },
    () => showStatus("Could not get device location.", "error"),
    { enableHighAccuracy: true, timeout: 10000 },
  );
}

function openAgrovetRegistration() {
  if (!state.token) {
    setAuthMode("signup");
    els.authModal.showModal();
    showStatus("Create an account or log in before registering your shop.");
    return;
  }
  if (state.myAgrovet && !isAdmin()) {
    showStatus("Your agrovet shop is already registered.");
    return;
  }
  els.agrovetModal.showModal();
}

function openProductForAgrovet(agrovetId) {
  state.productAgrovetId = agrovetId;
  els.productModal.showModal();
}

function navigateTo(route) {
  state.route = ["#agrovets", "#admin", "#jack"].includes(route) ? route : "#feed";
  if (window.location.hash !== state.route) {
    window.location.hash = state.route;
  }
  renderRoute();
}

function openAuth() {
  if (state.token) {
    handleLogout();
    return;
  }
  state.adminLogin = false;
  setAuthMode("login");
  els.authModal.showModal();
}

function openAdminAuth() {
  state.adminLogin = true;
  setAuthMode("login");
  els.authModal.showModal();
}

function wireEvents() {
  document.querySelectorAll(".tab").forEach(tab => {
    tab.addEventListener("click", () => {
      document.querySelectorAll(".tab").forEach(item => item.classList.remove("active"));
      tab.classList.add("active");
      state.filter = tab.dataset.filter;
      renderFeed();
    });
  });

  document.querySelectorAll("[data-close-modal]").forEach(button => {
    button.addEventListener("click", () => button.closest("dialog").close());
  });

  document.querySelectorAll('a[href="#feed"], a[href="#agrovets"], a[href="#jack"]').forEach(link => {
    link.addEventListener("click", event => {
      event.preventDefault();
      navigateTo(link.getAttribute("href"));
    });
  });

  els.authButton.addEventListener("click", openAuth);
  els.bottomAuthButton.addEventListener("click", openAuth);
  els.adminLoginButton.addEventListener("click", openAdminAuth);
  els.adminAddAgrovetButton.addEventListener("click", openAgrovetRegistration);
  els.toggleAuthMode.addEventListener("click", () =>
    setAuthMode(state.authMode === "login" ? "signup" : "login"),
  );
  els.authForm.addEventListener("submit", handleAuthSubmit);
  els.agrovetForm.addEventListener("submit", handleAgrovetSubmit);
  els.expertApplicationForm.addEventListener("submit", handleExpertApplicationSubmit);
  els.issueForm.addEventListener("submit", handleIssueSubmit);
  els.jackChatForm.addEventListener("submit", handleJackSubmit);
  els.jackKnowledgeForm.addEventListener("submit", handleJackKnowledgeSubmit);
  els.productForm.addEventListener("submit", handleProductSubmit);
  els.openAgrovetRegistration.addEventListener("click", openAgrovetRegistration);
  els.openExpertApplication.addEventListener("click", () => els.expertApplicationModal.showModal());
  els.openIssueModal.addEventListener("click", () => els.issueModal.showModal());
  els.openProductModal.addEventListener("click", () => {
    state.productAgrovetId = null;
    els.productModal.showModal();
  });
  els.startSellingButton.addEventListener("click", openAgrovetRegistration);
  els.sideAskButton.addEventListener("click", () => els.issueModal.showModal());
  els.bottomAskButton.addEventListener("click", () => els.issueModal.showModal());
  els.feedList.addEventListener("click", event => {
    const button = event.target.closest("[data-action]");
    if (!button) return;
    const issueId = button.dataset.issueId;
    if (button.dataset.action === "reply-comment") {
      if (!state.token) {
        setAuthMode("login");
        els.authModal.showModal();
        showStatus("Log in before replying.");
        return;
      }
      state.replyingCommentId = button.dataset.commentId;
      renderFeed();
      return;
    }
    if (button.dataset.action === "cancel-reply") {
      state.replyingCommentId = null;
      renderFeed();
      return;
    }
    if (button.dataset.action === "collapse") {
      state.expandedIssueId = null;
      state.expandedTab = null;
      state.activeIssue = null;
      state.replyingCommentId = null;
      renderFeed();
      return;
    }
    if (button.dataset.action === "copy-share") {
      shareIssue(issueId);
      return;
    }
    if (button.dataset.action === "vote") {
      handleVote(issueId, Number(button.dataset.voteValue));
      return;
    }
    if (button.dataset.action === "share") {
      openIssueDetail(issueId, "share");
      return;
    }
    openIssueDetail(issueId, button.dataset.action);
  });
  els.feedList.addEventListener("submit", event => {
    if (event.target.closest("[data-comment-form]")) {
      handleCommentSubmit(event);
      return;
    }
    if (event.target.closest("[data-recommendation-form]")) {
      handleRecommendationSubmit(event);
    }
  });
  els.mobileSearch.addEventListener("input", event => {
    state.search = event.currentTarget.value;
    renderFeed();
  });
  els.agrovetSearch.addEventListener("input", event => {
    state.shopSearch = event.currentTarget.value;
    renderAgrovetsPage();
  });
  els.issueImage.addEventListener("change", event => {
    const file = event.currentTarget.files?.[0];
    els.issueImagePreview.textContent = file ? file.name : "";
  });
  els.adminApplicationList.addEventListener("click", event => {
    const button = event.target.closest("[data-review-action]");
    if (!button) return;
    reviewExpertApplication(button.dataset.applicationId, button.dataset.reviewAction);
  });
  els.adminPageApplicationList.addEventListener("click", event => {
    const button = event.target.closest("[data-review-action]");
    if (!button) return;
    reviewExpertApplication(button.dataset.applicationId, button.dataset.reviewAction);
  });
  els.adminAgrovetList.addEventListener("click", event => {
    const button = event.target.closest("[data-admin-product-agrovet]");
    if (!button) return;
    openProductForAgrovet(button.dataset.adminProductAgrovet);
  });
  els.adminJackKnowledgeList.addEventListener("click", event => {
    const editButton = event.target.closest("[data-jack-knowledge-edit]");
    if (editButton) {
      editJackKnowledge(editButton.dataset.jackKnowledgeEdit);
      return;
    }
    const deleteButton = event.target.closest("[data-jack-knowledge-delete]");
    if (deleteButton) {
      deleteJackKnowledge(deleteButton.dataset.jackKnowledgeDelete);
    }
  });
  els.useDeviceLocation.addEventListener("click", useDeviceLocation);
  window.addEventListener("hashchange", () => {
    state.route = ["#agrovets", "#admin", "#jack"].includes(window.location.hash) ? window.location.hash : "#feed";
    renderRoute();
  });
}

async function init() {
  wireEvents();
  await loadCurrentUser();
  await loadExpertApplications();
  await loadJackKnowledge();
  await loadMyAgrovet();
  renderAuth();
  renderRoute();
  loadData();
}

init();
