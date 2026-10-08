// Generated from frontend/index.js by npm run build. Do not edit.
var __defProp = Object.defineProperty;
var __defNormalProp = (obj, key, value) => key in obj ? __defProp(obj, key, { enumerable: true, configurable: true, writable: true, value }) : obj[key] = value;
var __publicField = (obj, key, value) => __defNormalProp(obj, typeof key !== "symbol" ? key + "" : key, value);

// node_modules/@lit/reactive-element/css-tag.js
var t = globalThis;
var e = t.ShadowRoot && (void 0 === t.ShadyCSS || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype;
var s = Symbol();
var o = /* @__PURE__ */ new WeakMap();
var n = class {
  constructor(t3, e4, o5) {
    if (this._$cssResult$ = true, o5 !== s) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t3, this.t = e4;
  }
  get styleSheet() {
    let t3 = this.o;
    const s4 = this.t;
    if (e && void 0 === t3) {
      const e4 = void 0 !== s4 && 1 === s4.length;
      e4 && (t3 = o.get(s4)), void 0 === t3 && ((this.o = t3 = new CSSStyleSheet()).replaceSync(this.cssText), e4 && o.set(s4, t3));
    }
    return t3;
  }
  toString() {
    return this.cssText;
  }
};
var r = (t3) => new n("string" == typeof t3 ? t3 : t3 + "", void 0, s);
var i = (t3, ...e4) => {
  const o5 = 1 === t3.length ? t3[0] : e4.reduce((e5, s4, o6) => e5 + ((t4) => {
    if (true === t4._$cssResult$) return t4.cssText;
    if ("number" == typeof t4) return t4;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t4 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s4) + t3[o6 + 1], t3[0]);
  return new n(o5, t3, s);
};
var S = (s4, o5) => {
  if (e) s4.adoptedStyleSheets = o5.map((t3) => t3 instanceof CSSStyleSheet ? t3 : t3.styleSheet);
  else for (const e4 of o5) {
    const o6 = document.createElement("style"), n4 = t.litNonce;
    void 0 !== n4 && o6.setAttribute("nonce", n4), o6.textContent = e4.cssText, s4.appendChild(o6);
  }
};
var c = e ? (t3) => t3 : (t3) => t3 instanceof CSSStyleSheet ? ((t4) => {
  let e4 = "";
  for (const s4 of t4.cssRules) e4 += s4.cssText;
  return r(e4);
})(t3) : t3;

// node_modules/@lit/reactive-element/reactive-element.js
var { is: i2, defineProperty: e2, getOwnPropertyDescriptor: h, getOwnPropertyNames: r2, getOwnPropertySymbols: o2, getPrototypeOf: n2 } = Object;
var a = globalThis;
var c2 = a.trustedTypes;
var l = c2 ? c2.emptyScript : "";
var p = a.reactiveElementPolyfillSupport;
var d = (t3, s4) => t3;
var u = { toAttribute(t3, s4) {
  switch (s4) {
    case Boolean:
      t3 = t3 ? l : null;
      break;
    case Object:
    case Array:
      t3 = null == t3 ? t3 : JSON.stringify(t3);
  }
  return t3;
}, fromAttribute(t3, s4) {
  let i5 = t3;
  switch (s4) {
    case Boolean:
      i5 = null !== t3;
      break;
    case Number:
      i5 = null === t3 ? null : Number(t3);
      break;
    case Object:
    case Array:
      try {
        i5 = JSON.parse(t3);
      } catch (t4) {
        i5 = null;
      }
  }
  return i5;
} };
var f = (t3, s4) => !i2(t3, s4);
var b = { attribute: true, type: String, converter: u, reflect: false, useDefault: false, hasChanged: f };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), a.litPropertyMetadata ?? (a.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
var y = class extends HTMLElement {
  static addInitializer(t3) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t3);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t3, s4 = b) {
    if (s4.state && (s4.attribute = false), this._$Ei(), this.prototype.hasOwnProperty(t3) && ((s4 = Object.create(s4)).wrapped = true), this.elementProperties.set(t3, s4), !s4.noAccessor) {
      const i5 = Symbol(), h3 = this.getPropertyDescriptor(t3, i5, s4);
      void 0 !== h3 && e2(this.prototype, t3, h3);
    }
  }
  static getPropertyDescriptor(t3, s4, i5) {
    const { get: e4, set: r4 } = h(this.prototype, t3) ?? { get() {
      return this[s4];
    }, set(t4) {
      this[s4] = t4;
    } };
    return { get: e4, set(s5) {
      const h3 = e4?.call(this);
      r4?.call(this, s5), this.requestUpdate(t3, h3, i5);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t3) {
    return this.elementProperties.get(t3) ?? b;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d("elementProperties"))) return;
    const t3 = n2(this);
    t3.finalize(), void 0 !== t3.l && (this.l = [...t3.l]), this.elementProperties = new Map(t3.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d("finalized"))) return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d("properties"))) {
      const t4 = this.properties, s4 = [...r2(t4), ...o2(t4)];
      for (const i5 of s4) this.createProperty(i5, t4[i5]);
    }
    const t3 = this[Symbol.metadata];
    if (null !== t3) {
      const s4 = litPropertyMetadata.get(t3);
      if (void 0 !== s4) for (const [t4, i5] of s4) this.elementProperties.set(t4, i5);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t4, s4] of this.elementProperties) {
      const i5 = this._$Eu(t4, s4);
      void 0 !== i5 && this._$Eh.set(i5, t4);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s4) {
    const i5 = [];
    if (Array.isArray(s4)) {
      const e4 = new Set(s4.flat(1 / 0).reverse());
      for (const s5 of e4) i5.unshift(c(s5));
    } else void 0 !== s4 && i5.push(c(s4));
    return i5;
  }
  static _$Eu(t3, s4) {
    const i5 = s4.attribute;
    return false === i5 ? void 0 : "string" == typeof i5 ? i5 : "string" == typeof t3 ? t3.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t3) => this.enableUpdating = t3), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t3) => t3(this));
  }
  addController(t3) {
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t3), void 0 !== this.renderRoot && this.isConnected && t3.hostConnected?.();
  }
  removeController(t3) {
    this._$EO?.delete(t3);
  }
  _$E_() {
    const t3 = /* @__PURE__ */ new Map(), s4 = this.constructor.elementProperties;
    for (const i5 of s4.keys()) this.hasOwnProperty(i5) && (t3.set(i5, this[i5]), delete this[i5]);
    t3.size > 0 && (this._$Ep = t3);
  }
  createRenderRoot() {
    const t3 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S(t3, this.constructor.elementStyles), t3;
  }
  connectedCallback() {
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(true), this._$EO?.forEach((t3) => t3.hostConnected?.());
  }
  enableUpdating(t3) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t3) => t3.hostDisconnected?.());
  }
  attributeChangedCallback(t3, s4, i5) {
    this._$AK(t3, i5);
  }
  _$ET(t3, s4) {
    const i5 = this.constructor.elementProperties.get(t3), e4 = this.constructor._$Eu(t3, i5);
    if (void 0 !== e4 && true === i5.reflect) {
      const h3 = (void 0 !== i5.converter?.toAttribute ? i5.converter : u).toAttribute(s4, i5.type);
      this._$Em = t3, null == h3 ? this.removeAttribute(e4) : this.setAttribute(e4, h3), this._$Em = null;
    }
  }
  _$AK(t3, s4) {
    const i5 = this.constructor, e4 = i5._$Eh.get(t3);
    if (void 0 !== e4 && this._$Em !== e4) {
      const t4 = i5.getPropertyOptions(e4), h3 = "function" == typeof t4.converter ? { fromAttribute: t4.converter } : void 0 !== t4.converter?.fromAttribute ? t4.converter : u;
      this._$Em = e4;
      const r4 = h3.fromAttribute(s4, t4.type);
      this[e4] = r4 ?? this._$Ej?.get(e4) ?? r4, this._$Em = null;
    }
  }
  requestUpdate(t3, s4, i5, e4 = false, h3) {
    if (void 0 !== t3) {
      const r4 = this.constructor;
      if (false === e4 && (h3 = this[t3]), i5 ?? (i5 = r4.getPropertyOptions(t3)), !((i5.hasChanged ?? f)(h3, s4) || i5.useDefault && i5.reflect && h3 === this._$Ej?.get(t3) && !this.hasAttribute(r4._$Eu(t3, i5)))) return;
      this.C(t3, s4, i5);
    }
    false === this.isUpdatePending && (this._$ES = this._$EP());
  }
  C(t3, s4, { useDefault: i5, reflect: e4, wrapped: h3 }, r4) {
    i5 && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t3) && (this._$Ej.set(t3, r4 ?? s4 ?? this[t3]), true !== h3 || void 0 !== r4) || (this._$AL.has(t3) || (this.hasUpdated || i5 || (s4 = void 0), this._$AL.set(t3, s4)), true === e4 && this._$Em !== t3 && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t3));
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t4) {
      Promise.reject(t4);
    }
    const t3 = this.scheduleUpdate();
    return null != t3 && await t3, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [t5, s5] of this._$Ep) this[t5] = s5;
        this._$Ep = void 0;
      }
      const t4 = this.constructor.elementProperties;
      if (t4.size > 0) for (const [s5, i5] of t4) {
        const { wrapped: t5 } = i5, e4 = this[s5];
        true !== t5 || this._$AL.has(s5) || void 0 === e4 || this.C(s5, void 0, i5, e4);
      }
    }
    let t3 = false;
    const s4 = this._$AL;
    try {
      t3 = this.shouldUpdate(s4), t3 ? (this.willUpdate(s4), this._$EO?.forEach((t4) => t4.hostUpdate?.()), this.update(s4)) : this._$EM();
    } catch (s5) {
      throw t3 = false, this._$EM(), s5;
    }
    t3 && this._$AE(s4);
  }
  willUpdate(t3) {
  }
  _$AE(t3) {
    this._$EO?.forEach((t4) => t4.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t3)), this.updated(t3);
  }
  _$EM() {
    this._$AL = /* @__PURE__ */ new Map(), this.isUpdatePending = false;
  }
  get updateComplete() {
    return this.getUpdateComplete();
  }
  getUpdateComplete() {
    return this._$ES;
  }
  shouldUpdate(t3) {
    return true;
  }
  update(t3) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t4) => this._$ET(t4, this[t4]))), this._$EM();
  }
  updated(t3) {
  }
  firstUpdated(t3) {
  }
};
y.elementStyles = [], y.shadowRootOptions = { mode: "open" }, y[d("elementProperties")] = /* @__PURE__ */ new Map(), y[d("finalized")] = /* @__PURE__ */ new Map(), p?.({ ReactiveElement: y }), (a.reactiveElementVersions ?? (a.reactiveElementVersions = [])).push("2.1.2");

// node_modules/lit-html/lit-html.js
var t2 = globalThis;
var i3 = (t3) => t3;
var s2 = t2.trustedTypes;
var e3 = s2 ? s2.createPolicy("lit-html", { createHTML: (t3) => t3 }) : void 0;
var h2 = "$lit$";
var o3 = `lit$${Math.random().toFixed(9).slice(2)}$`;
var n3 = "?" + o3;
var r3 = `<${n3}>`;
var l2 = document;
var c3 = () => l2.createComment("");
var a2 = (t3) => null === t3 || "object" != typeof t3 && "function" != typeof t3;
var u2 = Array.isArray;
var d2 = (t3) => u2(t3) || "function" == typeof t3?.[Symbol.iterator];
var f2 = "[ 	\n\f\r]";
var v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g;
var _ = /-->/g;
var m = />/g;
var p2 = RegExp(`>|${f2}(?:([^\\s"'>=/]+)(${f2}*=${f2}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g");
var g = /'/g;
var $ = /"/g;
var y2 = /^(?:script|style|textarea|title)$/i;
var x = (t3) => (i5, ...s4) => ({ _$litType$: t3, strings: i5, values: s4 });
var b2 = x(1);
var w = x(2);
var T = x(3);
var E = Symbol.for("lit-noChange");
var A = Symbol.for("lit-nothing");
var C = /* @__PURE__ */ new WeakMap();
var P = l2.createTreeWalker(l2, 129);
function V(t3, i5) {
  if (!u2(t3) || !t3.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return void 0 !== e3 ? e3.createHTML(i5) : i5;
}
var N = (t3, i5) => {
  const s4 = t3.length - 1, e4 = [];
  let n4, l3 = 2 === i5 ? "<svg>" : 3 === i5 ? "<math>" : "", c4 = v;
  for (let i6 = 0; i6 < s4; i6++) {
    const s5 = t3[i6];
    let a3, u3, d3 = -1, f3 = 0;
    for (; f3 < s5.length && (c4.lastIndex = f3, u3 = c4.exec(s5), null !== u3); ) f3 = c4.lastIndex, c4 === v ? "!--" === u3[1] ? c4 = _ : void 0 !== u3[1] ? c4 = m : void 0 !== u3[2] ? (y2.test(u3[2]) && (n4 = RegExp("</" + u3[2], "g")), c4 = p2) : void 0 !== u3[3] && (c4 = p2) : c4 === p2 ? ">" === u3[0] ? (c4 = n4 ?? v, d3 = -1) : void 0 === u3[1] ? d3 = -2 : (d3 = c4.lastIndex - u3[2].length, a3 = u3[1], c4 = void 0 === u3[3] ? p2 : '"' === u3[3] ? $ : g) : c4 === $ || c4 === g ? c4 = p2 : c4 === _ || c4 === m ? c4 = v : (c4 = p2, n4 = void 0);
    const x2 = c4 === p2 && t3[i6 + 1].startsWith("/>") ? " " : "";
    l3 += c4 === v ? s5 + r3 : d3 >= 0 ? (e4.push(a3), s5.slice(0, d3) + h2 + s5.slice(d3) + o3 + x2) : s5 + o3 + (-2 === d3 ? i6 : x2);
  }
  return [V(t3, l3 + (t3[s4] || "<?>") + (2 === i5 ? "</svg>" : 3 === i5 ? "</math>" : "")), e4];
};
var S2 = class _S {
  constructor({ strings: t3, _$litType$: i5 }, e4) {
    let r4;
    this.parts = [];
    let l3 = 0, a3 = 0;
    const u3 = t3.length - 1, d3 = this.parts, [f3, v2] = N(t3, i5);
    if (this.el = _S.createElement(f3, e4), P.currentNode = this.el.content, 2 === i5 || 3 === i5) {
      const t4 = this.el.content.firstChild;
      t4.replaceWith(...t4.childNodes);
    }
    for (; null !== (r4 = P.nextNode()) && d3.length < u3; ) {
      if (1 === r4.nodeType) {
        if (r4.hasAttributes()) for (const t4 of r4.getAttributeNames()) if (t4.endsWith(h2)) {
          const i6 = v2[a3++], s4 = r4.getAttribute(t4).split(o3), e5 = /([.?@])?(.*)/.exec(i6);
          d3.push({ type: 1, index: l3, name: e5[2], strings: s4, ctor: "." === e5[1] ? I : "?" === e5[1] ? L : "@" === e5[1] ? z : H }), r4.removeAttribute(t4);
        } else t4.startsWith(o3) && (d3.push({ type: 6, index: l3 }), r4.removeAttribute(t4));
        if (y2.test(r4.tagName)) {
          const t4 = r4.textContent.split(o3), i6 = t4.length - 1;
          if (i6 > 0) {
            r4.textContent = s2 ? s2.emptyScript : "";
            for (let s4 = 0; s4 < i6; s4++) r4.append(t4[s4], c3()), P.nextNode(), d3.push({ type: 2, index: ++l3 });
            r4.append(t4[i6], c3());
          }
        }
      } else if (8 === r4.nodeType) if (r4.data === n3) d3.push({ type: 2, index: l3 });
      else {
        let t4 = -1;
        for (; -1 !== (t4 = r4.data.indexOf(o3, t4 + 1)); ) d3.push({ type: 7, index: l3 }), t4 += o3.length - 1;
      }
      l3++;
    }
  }
  static createElement(t3, i5) {
    const s4 = l2.createElement("template");
    return s4.innerHTML = t3, s4;
  }
};
function M(t3, i5, s4 = t3, e4) {
  if (i5 === E) return i5;
  let h3 = void 0 !== e4 ? s4._$Co?.[e4] : s4._$Cl;
  const o5 = a2(i5) ? void 0 : i5._$litDirective$;
  return h3?.constructor !== o5 && (h3?._$AO?.(false), void 0 === o5 ? h3 = void 0 : (h3 = new o5(t3), h3._$AT(t3, s4, e4)), void 0 !== e4 ? (s4._$Co ?? (s4._$Co = []))[e4] = h3 : s4._$Cl = h3), void 0 !== h3 && (i5 = M(t3, h3._$AS(t3, i5.values), h3, e4)), i5;
}
var R = class {
  constructor(t3, i5) {
    this._$AV = [], this._$AN = void 0, this._$AD = t3, this._$AM = i5;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t3) {
    const { el: { content: i5 }, parts: s4 } = this._$AD, e4 = (t3?.creationScope ?? l2).importNode(i5, true);
    P.currentNode = e4;
    let h3 = P.nextNode(), o5 = 0, n4 = 0, r4 = s4[0];
    for (; void 0 !== r4; ) {
      if (o5 === r4.index) {
        let i6;
        2 === r4.type ? i6 = new k(h3, h3.nextSibling, this, t3) : 1 === r4.type ? i6 = new r4.ctor(h3, r4.name, r4.strings, this, t3) : 6 === r4.type && (i6 = new Z(h3, this, t3)), this._$AV.push(i6), r4 = s4[++n4];
      }
      o5 !== r4?.index && (h3 = P.nextNode(), o5++);
    }
    return P.currentNode = l2, e4;
  }
  p(t3) {
    let i5 = 0;
    for (const s4 of this._$AV) void 0 !== s4 && (void 0 !== s4.strings ? (s4._$AI(t3, s4, i5), i5 += s4.strings.length - 2) : s4._$AI(t3[i5])), i5++;
  }
};
var k = class _k {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t3, i5, s4, e4) {
    this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t3, this._$AB = i5, this._$AM = s4, this.options = e4, this._$Cv = e4?.isConnected ?? true;
  }
  get parentNode() {
    let t3 = this._$AA.parentNode;
    const i5 = this._$AM;
    return void 0 !== i5 && 11 === t3?.nodeType && (t3 = i5.parentNode), t3;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t3, i5 = this) {
    t3 = M(this, t3, i5), a2(t3) ? t3 === A || null == t3 || "" === t3 ? (this._$AH !== A && this._$AR(), this._$AH = A) : t3 !== this._$AH && t3 !== E && this._(t3) : void 0 !== t3._$litType$ ? this.$(t3) : void 0 !== t3.nodeType ? this.T(t3) : d2(t3) ? this.k(t3) : this._(t3);
  }
  O(t3) {
    return this._$AA.parentNode.insertBefore(t3, this._$AB);
  }
  T(t3) {
    this._$AH !== t3 && (this._$AR(), this._$AH = this.O(t3));
  }
  _(t3) {
    this._$AH !== A && a2(this._$AH) ? this._$AA.nextSibling.data = t3 : this.T(l2.createTextNode(t3)), this._$AH = t3;
  }
  $(t3) {
    const { values: i5, _$litType$: s4 } = t3, e4 = "number" == typeof s4 ? this._$AC(t3) : (void 0 === s4.el && (s4.el = S2.createElement(V(s4.h, s4.h[0]), this.options)), s4);
    if (this._$AH?._$AD === e4) this._$AH.p(i5);
    else {
      const t4 = new R(e4, this), s5 = t4.u(this.options);
      t4.p(i5), this.T(s5), this._$AH = t4;
    }
  }
  _$AC(t3) {
    let i5 = C.get(t3.strings);
    return void 0 === i5 && C.set(t3.strings, i5 = new S2(t3)), i5;
  }
  k(t3) {
    u2(this._$AH) || (this._$AH = [], this._$AR());
    const i5 = this._$AH;
    let s4, e4 = 0;
    for (const h3 of t3) e4 === i5.length ? i5.push(s4 = new _k(this.O(c3()), this.O(c3()), this, this.options)) : s4 = i5[e4], s4._$AI(h3), e4++;
    e4 < i5.length && (this._$AR(s4 && s4._$AB.nextSibling, e4), i5.length = e4);
  }
  _$AR(t3 = this._$AA.nextSibling, s4) {
    for (this._$AP?.(false, true, s4); t3 !== this._$AB; ) {
      const s5 = i3(t3).nextSibling;
      i3(t3).remove(), t3 = s5;
    }
  }
  setConnected(t3) {
    void 0 === this._$AM && (this._$Cv = t3, this._$AP?.(t3));
  }
};
var H = class {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t3, i5, s4, e4, h3) {
    this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t3, this.name = i5, this._$AM = e4, this.options = h3, s4.length > 2 || "" !== s4[0] || "" !== s4[1] ? (this._$AH = Array(s4.length - 1).fill(new String()), this.strings = s4) : this._$AH = A;
  }
  _$AI(t3, i5 = this, s4, e4) {
    const h3 = this.strings;
    let o5 = false;
    if (void 0 === h3) t3 = M(this, t3, i5, 0), o5 = !a2(t3) || t3 !== this._$AH && t3 !== E, o5 && (this._$AH = t3);
    else {
      const e5 = t3;
      let n4, r4;
      for (t3 = h3[0], n4 = 0; n4 < h3.length - 1; n4++) r4 = M(this, e5[s4 + n4], i5, n4), r4 === E && (r4 = this._$AH[n4]), o5 || (o5 = !a2(r4) || r4 !== this._$AH[n4]), r4 === A ? t3 = A : t3 !== A && (t3 += (r4 ?? "") + h3[n4 + 1]), this._$AH[n4] = r4;
    }
    o5 && !e4 && this.j(t3);
  }
  j(t3) {
    t3 === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t3 ?? "");
  }
};
var I = class extends H {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t3) {
    this.element[this.name] = t3 === A ? void 0 : t3;
  }
};
var L = class extends H {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t3) {
    this.element.toggleAttribute(this.name, !!t3 && t3 !== A);
  }
};
var z = class extends H {
  constructor(t3, i5, s4, e4, h3) {
    super(t3, i5, s4, e4, h3), this.type = 5;
  }
  _$AI(t3, i5 = this) {
    if ((t3 = M(this, t3, i5, 0) ?? A) === E) return;
    const s4 = this._$AH, e4 = t3 === A && s4 !== A || t3.capture !== s4.capture || t3.once !== s4.once || t3.passive !== s4.passive, h3 = t3 !== A && (s4 === A || e4);
    e4 && this.element.removeEventListener(this.name, this, s4), h3 && this.element.addEventListener(this.name, this, t3), this._$AH = t3;
  }
  handleEvent(t3) {
    "function" == typeof this._$AH ? this._$AH.call(this.options?.host ?? this.element, t3) : this._$AH.handleEvent(t3);
  }
};
var Z = class {
  constructor(t3, i5, s4) {
    this.element = t3, this.type = 6, this._$AN = void 0, this._$AM = i5, this.options = s4;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t3) {
    M(this, t3);
  }
};
var B = t2.litHtmlPolyfillSupport;
B?.(S2, k), (t2.litHtmlVersions ?? (t2.litHtmlVersions = [])).push("3.3.2");
var D = (t3, i5, s4) => {
  const e4 = s4?.renderBefore ?? i5;
  let h3 = e4._$litPart$;
  if (void 0 === h3) {
    const t4 = s4?.renderBefore ?? null;
    e4._$litPart$ = h3 = new k(i5.insertBefore(c3(), t4), t4, void 0, s4 ?? {});
  }
  return h3._$AI(t3), h3;
};

// node_modules/lit-element/lit-element.js
var s3 = globalThis;
var i4 = class extends y {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var _a;
    const t3 = super.createRenderRoot();
    return (_a = this.renderOptions).renderBefore ?? (_a.renderBefore = t3.firstChild), t3;
  }
  update(t3) {
    const r4 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t3), this._$Do = D(r4, this.renderRoot, this.renderOptions);
  }
  connectedCallback() {
    super.connectedCallback(), this._$Do?.setConnected(true);
  }
  disconnectedCallback() {
    super.disconnectedCallback(), this._$Do?.setConnected(false);
  }
  render() {
    return E;
  }
};
i4._$litElement$ = true, i4["finalized"] = true, s3.litElementHydrateSupport?.({ LitElement: i4 });
var o4 = s3.litElementPolyfillSupport;
o4?.({ LitElement: i4 });
(s3.litElementVersions ?? (s3.litElementVersions = [])).push("4.2.2");

// frontend/herald-card.js
window.customCards = window.customCards || [];
[
  {
    type: "herald-card",
    name: "Herald Card",
    description: "\u041F\u043E\u043B\u043D\u0430\u044F \u043A\u0430\u0440\u0442\u043E\u0447\u043A\u0430 Herald",
    preview: true
  },
  {
    type: "ha-herald-general",
    name: "Herald: \u041E\u0431\u0449\u0435\u0435",
    description: "\u041A\u0440\u0430\u0442\u043A\u0438\u0439 \u0441\u0442\u0430\u0442\u0443\u0441 \u0438 \u0441\u0432\u043E\u0434\u043A\u0430 Herald",
    preview: true
  },
  {
    type: "ha-herald-policies",
    name: "Herald: \u041F\u043E\u043B\u0438\u0442\u0438\u043A\u0438",
    description: "\u041F\u043E\u043B\u0438\u0442\u0438\u043A\u0438 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0439 Herald",
    preview: true
  },
  {
    type: "ha-herald-policy-guide",
    name: "Herald: \u041F\u0430\u043C\u044F\u0442\u043A\u0430",
    description: "\u041A\u0440\u0430\u0442\u043A\u0430\u044F \u043F\u0430\u043C\u044F\u0442\u043A\u0430 \u043F\u043E policy-\u043E\u0431\u044A\u0435\u043A\u0442\u0430\u043C Herald",
    preview: true
  },
  {
    type: "ha-herald-flows",
    name: "Herald: \u041F\u043E\u0442\u043E\u043A\u0438",
    description: "\u041F\u043E\u0442\u043E\u043A\u0438 \u0438 \u0437\u0430\u0433\u043B\u0443\u0448\u0435\u043D\u0438\u0435 Herald",
    preview: true
  },
  {
    type: "ha-herald-languages",
    name: "Herald: \u042F\u0437\u044B\u043A\u0438",
    description: "\u042F\u0437\u044B\u043A\u0438 \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u0435\u0439 Herald",
    preview: true
  },
  {
    type: "ha-herald-characters",
    name: "Herald: \u041F\u0435\u0440\u0441\u043E\u043D\u0430\u0436\u0438",
    description: "\u041F\u0435\u0440\u0441\u043E\u043D\u0430\u0436\u0438 \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u0435\u0439 Herald",
    preview: true
  },
  {
    type: "ha-herald-mute",
    name: "Herald: \u0422\u0438\u0448\u0438\u043D\u0430",
    description: "\u0422\u043E\u0447\u0435\u0447\u043D\u043E\u0435 \u0437\u0430\u0433\u043B\u0443\u0448\u0435\u043D\u0438\u0435 Herald",
    preview: true
  },
  {
    type: "ha-herald-rooms",
    name: "Herald: \u041A\u043E\u043C\u043D\u0430\u0442\u044B",
    description: "\u041A\u043E\u043C\u043D\u0430\u0442\u044B \u0438 fallback-\u043F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0430\u0442\u0435\u043B\u0438 Herald",
    preview: true
  },
  {
    type: "ha-herald-queue",
    name: "Herald: \u041E\u0447\u0435\u0440\u0435\u0434\u044C",
    description: "\u041E\u0447\u0435\u0440\u0435\u0434\u044C \u0441\u043E\u0431\u044B\u0442\u0438\u0439 Herald",
    preview: true
  },
  {
    type: "ha-herald-feed",
    name: "Herald: \u041B\u0435\u043D\u0442\u0430",
    description: "\u041B\u0435\u043D\u0442\u0430 \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0438 Herald",
    preview: true
  },
  {
    type: "ha-herald-recent",
    name: "Herald: \u041F\u043E\u0441\u043B\u0435\u0434\u043D\u0438\u0435",
    description: "\u041F\u043E\u0441\u043B\u0435\u0434\u043D\u0438\u0435 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F Herald",
    preview: true
  },
  {
    type: "ha-herald-controls",
    name: "Herald: \u0423\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u0438\u0435",
    description: "\u0421\u043E\u0441\u0442\u0430\u0432\u043D\u0430\u044F \u043A\u0430\u0440\u0442\u043E\u0447\u043A\u0430 \u0443\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u0438\u044F Herald",
    preview: true
  },
  {
    type: "ha-herald-overview",
    name: "Herald: \u041E\u0431\u0437\u043E\u0440",
    description: "\u0421\u043E\u0441\u0442\u0430\u0432\u043D\u0430\u044F \u043E\u0431\u0437\u043E\u0440\u043D\u0430\u044F \u043A\u0430\u0440\u0442\u043E\u0447\u043A\u0430 Herald",
    preview: true
  }
].forEach((card) => {
  if (!window.customCards.some((item) => item.type === card.type)) {
    window.customCards.push({
      ...card,
      documentationURL: "https://github.com/Mesteriis/ha-herald"
    });
  }
});
var DEFAULT_LANGUAGES = ["ru", "en", "es", "fr"];
var DEFAULT_STATUS_ENTITY = "sensor.herald_notification_center_status";
var DEFAULT_TODAY_ENTITY = "sensor.herald_notification_center_notifications_today";
var DEFAULT_LAST_ENTITY = "sensor.herald_notification_center_last_notification";
var DEFAULT_QUEUE_ENTITY = "sensor.herald_notification_center_queue_size";
var POLICY_PAGE_SIZE = 12;
var HeraldCard = class extends i4 {
  constructor() {
    super(...arguments);
    this._busyFlow = "";
    this._busyPolicy = "";
    this._policyDrafts = {};
    this._policySearch = "";
    this._policyFamily = "all";
    this._policyScope = "all";
    this._policyPage = 1;
    this._policyExpanded = "";
    this._policySaved = {};
    this._policyFeedback = {};
    this._policyPreviews = {};
    this._policyScenarios = {};
    this._policyRevisions = {};
    this._previewSequence = 0;
    this._controlActions = {};
    this._controlTimers = /* @__PURE__ */ new Map();
    this._controlSequence = 0;
    this._configurationSequence = 0;
    this._configurationBusy = false;
    this._configurationResponse = null;
    this._configurationFeedback = null;
  }
  setConfig(config) {
    this._clearControlActions();
    this._invalidateConfiguration();
    this._config = {
      ...config,
      view_mode: config.view_mode || this.constructor.viewMode || "full",
      status_entity: config.status_entity || DEFAULT_STATUS_ENTITY,
      today_entity: config.today_entity || DEFAULT_TODAY_ENTITY,
      last_entity: config.last_entity || DEFAULT_LAST_ENTITY,
      queue_entity: config.queue_entity || DEFAULT_QUEUE_ENTITY
    };
    if (config.initial_policy_key) {
      this._policyExpanded = config.initial_policy_key;
      this._policySearch = config.initial_policy_key;
      this._policyPage = 1;
    }
  }
  willUpdate(changed) {
    if (changed.has("hass")) this._reconcileControlActions();
  }
  disconnectedCallback() {
    super.disconnectedCallback();
    this._clearControlActions();
    this._invalidateConfiguration();
  }
  getCardSize() {
    const mode = this._config?.view_mode || this.constructor.viewMode || "full";
    if (["general", "flows", "languages", "characters", "mute", "rooms", "queue", "feed", "recent", "policy-guide"].includes(mode)) {
      return 3;
    }
    if (mode === "policies") {
      return 8;
    }
    return 6;
  }
  render() {
    if (!this.hass || !this._config) {
      return b2`<ha-card>Loading…</ha-card>`;
    }
    const today = this.hass.states[this._config.today_entity ?? ""];
    const last = this.hass.states[this._config.last_entity ?? ""];
    const queue = this.hass.states[this._config.queue_entity ?? ""];
    const status = this.hass.states[this._config.status_entity ?? DEFAULT_STATUS_ENTITY];
    if (!today || !last || !queue || !status) {
      return b2`<ha-card><div class="shell">Сущности Herald сейчас недоступны.</div></ha-card>`;
    }
    const recent = today.attributes.recent_notifications ?? [];
    const dashboardFeed = today.attributes.dashboard_feed ?? queue.attributes.dashboard_feed ?? [];
    const queuedNotifications = queue.attributes.queued_notifications ?? [];
    const flowStates = queue.attributes.flow_states ?? {};
    const snoozedFlows = queue.attributes.snoozed_flows ?? {};
    const userControlEntities = queue.attributes.control_entities?.users ?? [];
    const dedupe = (items) => [...new Set(items)];
    const languageEntities = dedupe([
      ...this._config.language_entities ?? [],
      ...userControlEntities.filter((entityId) => entityId.endsWith("_language"))
    ]);
    const characterEntities = dedupe(
      userControlEntities.filter((entityId) => entityId.endsWith("_character"))
    );
    const muteEntities = dedupe(
      userControlEntities.filter((entityId) => entityId.endsWith("_silent"))
    );
    const notificationRegistry = status.attributes.notification_registry?.items ?? [];
    const notificationSummary = status.attributes.notification_registry_summary ?? {};
    const policyFamilies = [...new Set(notificationRegistry.map((item) => item.family).filter(Boolean))].sort();
    const filteredRegistry = this._filterPolicies(notificationRegistry);
    const policyPage = this._paginatePolicies(filteredRegistry);
    const roomEntities = this._config.room_entities ?? [];
    const renderEmptySection = (title, subtitle, message, panelClass) => this._renderPanelCard(
      title,
      subtitle,
      b2`<div class="empty">${message}</div>`,
      A,
      panelClass
    );
    const heroCard = b2`
      <ha-card class="panel hero-panel">
        <div class="panel-shell">
          <div class="hero">
            <div>
              <p class="eyebrow">Herald</p>
              <h2>${this._config.title ?? "\u0426\u0435\u043D\u0442\u0440 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0439 Herald"}</h2>
              <p class="subhead">Нативная карточка управления уведомлениями: статус, очередь, пользователи, комнаты и последние события.</p>
            </div>
            <div class="stats">
              ${this._renderStat("\u0421\u0435\u0433\u043E\u0434\u043D\u044F", today.state)}
              ${this._renderStat("\u041E\u0447\u0435\u0440\u0435\u0434\u044C", queue.state)}
              ${this._renderStat("\u041F\u043E\u0441\u043B\u0435\u0434\u043D\u0435\u0435", last.state)}
            </div>
          </div>
          ${this._renderConfigurationOverview()}
        </div>
      </ha-card>
    `;
    const channelsSection = this._renderChannels();
    const policySection = notificationRegistry.length ? this._renderPanelCard(
      "\u041F\u0440\u0430\u0432\u0438\u043B\u0430 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0439",
      "\u0412\u044B\u0431\u0435\u0440\u0438\u0442\u0435 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0435, \u043D\u0430\u0441\u0442\u0440\u043E\u0439\u0442\u0435 \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0443 \u0438 \u043F\u0440\u043E\u0432\u0435\u0440\u044C\u0442\u0435 \u0440\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442.",
      b2`
        <div class="stats compact">
          ${this._renderStat("\u0412\u0441\u0435\u0433\u043E", notificationSummary.count ?? notificationRegistry.length)}
          ${this._renderStat("\u0412\u043A\u043B\u044E\u0447\u0435\u043D\u043E", notificationSummary.enabled_count ?? "\u043D\u0435\u0442")}
          ${this._renderStat("\u0412\u044B\u043A\u043B\u044E\u0447\u0435\u043D\u043E", notificationSummary.disabled_count ?? "\u043D\u0435\u0442")}
          ${this._renderStat("\u041A\u0430\u0441\u0442\u043E\u043C", notificationSummary.customized_count ?? "\u043D\u0435\u0442")}
          ${this._renderStat("\u0424\u0438\u043B\u044C\u0442\u0440", filteredRegistry.length)}
          ${this._renderStat("\u0421\u0442\u0440\u0430\u043D\u0438\u0446\u0430", policyPage.totalPages ? `${policyPage.page}/${policyPage.totalPages}` : "0/0")}
        </div>
        <div class="policy-toolbar">
          <label class="language-card policy-filter">
            <span>Поиск</span>
            <input
              .value=${this._policySearch}
              placeholder="стиралка, тариф, гости, камеры..."
              @input=${(event) => this._setPolicySearch(event.target.value)}
            />
          </label>
          <label class="language-card policy-filter">
            <span>Семейство</span>
            <select .value=${this._policyFamily} @change=${(event) => this._setPolicyFamily(event.target.value)}>
              <option value="all">Все</option>
              ${policyFamilies.map((family) => b2`<option value=${family}>${this._friendlyFamilyLabel(family)}</option>`)}
            </select>
          </label>
          <label class="language-card policy-filter">
            <span>Срез</span>
            <select .value=${this._policyScope} @change=${(event) => this._setPolicyScope(event.target.value)}>
              <option value="all">Все</option>
              <option value="active">Активные</option>
              <option value="attention">Требуют внимания</option>
              <option value="customized">Переопределенные</option>
              <option value="disabled">Отключенные</option>
            </select>
          </label>
        </div>
        ${policyPage.items.length ? this._renderPolicyTable(policyPage, filteredRegistry.length) : b2`<div class="empty">По текущему фильтру уведомлений нет.</div>`}
      `,
      b2`
        <button class="secondary-action" @click=${() => this._refreshPolicies()}>
          Обновить реестр
        </button>
      `,
      "policy-panel"
    ) : A;
    const policyGuideSection = notificationRegistry.length ? this._renderPanelCard(
      "\u041A\u0430\u043A \u043D\u0430\u0441\u0442\u0440\u043E\u0438\u0442\u044C \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0435",
      "\u041E\u0431\u0449\u0435\u0435 \u043F\u0440\u0430\u0432\u0438\u043B\u043E, \u043B\u0438\u0447\u043D\u043E\u0435 \u0438\u0441\u043A\u043B\u044E\u0447\u0435\u043D\u0438\u0435 \u0438 \u043F\u0440\u043E\u0432\u0435\u0440\u043A\u0430 \u0440\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442\u0430",
      b2`
        <div class="notification">
          <p>Открой уведомление и выбери способ доставки. «По общему правилу» учитывает поток, присутствие и общие настройки. «Выбрать каналы» задаёт свой список; пустой список означает отсутствие доставки. Проверь черновик без отправки, затем сохрани. Дополнительные параметры нужны для отдельных исключений.</p>
        </div>
      `,
      A,
      "policy-guide-panel"
    ) : A;
    const flowsSection = this._renderPanelCard(
      "\u041F\u043E\u0442\u043E\u043A\u0438",
      "\u0412\u0440\u0435\u043C\u0435\u043D\u043D\u043E\u0435 \u0432\u043A\u043B\u044E\u0447\u0435\u043D\u0438\u0435 \u0438 \u0437\u0430\u0433\u043B\u0443\u0448\u0435\u043D\u0438\u0435 \u043F\u043E\u0442\u043E\u043A\u043E\u0432",
      b2`
        <div class="flow-grid">
          ${Object.entries(flowStates).map(([flow, enabled]) => this._renderFlow(flow, enabled, snoozedFlows[flow]))}
        </div>
      `,
      A,
      "flows-panel"
    );
    const languagesSection = languageEntities.length ? this._renderPanelCard(
      "\u042F\u0437\u044B\u043A\u0438",
      "\u042F\u0437\u044B\u043A \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0439 \u043F\u043E \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044F\u043C",
      b2`
        <div class="language-grid">
          ${languageEntities.map((entityId) => this._renderLanguage(entityId))}
        </div>
      `,
      A,
      "languages-panel"
    ) : renderEmptySection("\u042F\u0437\u044B\u043A\u0438", "\u042F\u0437\u044B\u043A \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0439 \u043F\u043E \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044F\u043C", "\u041F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044C\u0441\u043A\u0438\u0435 \u044F\u0437\u044B\u043A\u043E\u0432\u044B\u0435 \u043A\u043E\u043D\u0442\u0440\u043E\u043B\u044B \u043F\u043E\u043A\u0430 \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D\u044B.", "languages-panel");
    const charactersSection = characterEntities.length ? this._renderPanelCard(
      "\u041F\u0435\u0440\u0441\u043E\u043D\u0430\u0436\u0438",
      "\u0418\u0418-\u043F\u0435\u0440\u0441\u043E\u043D\u0430\u0436 \u043F\u043E \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044F\u043C",
      b2`
        <div class="character-grid">
          ${characterEntities.map((entityId) => this._renderCharacter(entityId))}
        </div>
      `,
      A,
      "characters-panel"
    ) : renderEmptySection("\u041F\u0435\u0440\u0441\u043E\u043D\u0430\u0436\u0438", "\u0418\u0418-\u043F\u0435\u0440\u0441\u043E\u043D\u0430\u0436 \u043F\u043E \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044F\u043C", "\u041F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044C\u0441\u043A\u0438\u0435 \u043F\u0435\u0440\u0441\u043E\u043D\u0430\u0436\u0438 \u043F\u043E\u043A\u0430 \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D\u044B.", "characters-panel");
    const muteSection = muteEntities.length ? this._renderPanelCard(
      "\u0417\u0430\u0433\u043B\u0443\u0448\u0435\u043D\u0438\u0435",
      "\u0422\u043E\u0447\u0435\u0447\u043D\u043E\u0435 \u043E\u0442\u043A\u043B\u044E\u0447\u0435\u043D\u0438\u0435 \u0437\u0432\u0443\u043A\u0430 \u043F\u043E \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044F\u043C",
      b2`
        <div class="mute-grid">
          ${muteEntities.map((entityId) => this._renderMute(entityId))}
        </div>
      `,
      A,
      "mute-panel"
    ) : renderEmptySection("\u0417\u0430\u0433\u043B\u0443\u0448\u0435\u043D\u0438\u0435", "\u0422\u043E\u0447\u0435\u0447\u043D\u043E\u0435 \u043E\u0442\u043A\u043B\u044E\u0447\u0435\u043D\u0438\u0435 \u0437\u0432\u0443\u043A\u0430 \u043F\u043E \u043F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u044F\u043C", "\u041F\u0435\u0440\u0441\u043E\u043D\u0430\u043B\u044C\u043D\u044B\u0435 \u043F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0430\u0442\u0435\u043B\u0438 \u0442\u0438\u0448\u0438\u043D\u044B \u043F\u043E\u043A\u0430 \u043D\u0435 \u043D\u0430\u0439\u0434\u0435\u043D\u044B.", "mute-panel");
    const roomsSection = roomEntities.length ? this._renderPanelCard(
      "\u041A\u043E\u043C\u043D\u0430\u0442\u044B",
      "\u041A\u043E\u043C\u043D\u0430\u0442\u044B, \u043F\u0440\u0438\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u0435 \u0438 fallback-\u043F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0430\u0442\u0435\u043B\u0438 Herald",
      b2`
        <div class="room-grid">
          ${roomEntities.map((item) => this._renderRoom(item))}
        </div>
      `,
      A,
      "rooms-panel"
    ) : renderEmptySection("\u041A\u043E\u043C\u043D\u0430\u0442\u044B", "\u041A\u043E\u043C\u043D\u0430\u0442\u044B, \u043F\u0440\u0438\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u0435 \u0438 fallback-\u043F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0430\u0442\u0435\u043B\u0438 Herald", "\u041A\u043E\u043C\u043D\u0430\u0442\u043D\u044B\u0435 \u043A\u043E\u043D\u0442\u0440\u043E\u043B\u044B \u043F\u043E\u043A\u0430 \u043D\u0435 \u043D\u0430\u0441\u0442\u0440\u043E\u0435\u043D\u044B.", "rooms-panel");
    const queueSection = this._renderPanelCard(
      "\u041E\u0447\u0435\u0440\u0435\u0434\u044C",
      "\u0421\u043E\u0431\u044B\u0442\u0438\u044F, \u043A\u043E\u0442\u043E\u0440\u044B\u0435 \u0436\u0434\u0443\u0442 \u043E\u0442\u043F\u0440\u0430\u0432\u043A\u0438 \u0438\u043B\u0438 \u0441\u0432\u043E\u0434\u043A\u0438",
      b2`
        <div class="list">
          ${queuedNotifications.length ? queuedNotifications.slice(0, 8).map((item) => this._renderQueuedItem(item)) : b2`<div class="empty">Очередь сейчас пуста.</div>`}
        </div>
      `,
      A,
      "queue-panel"
    );
    const dashboardFeedSection = this._renderPanelCard(
      "\u041B\u0435\u043D\u0442\u0430 \u043F\u0430\u043D\u0435\u043B\u0438",
      "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F, \u0434\u043E\u0441\u0442\u0430\u0432\u043B\u0435\u043D\u043D\u044B\u0435 \u0432 \u043A\u0430\u043D\u0430\u043B Herald dashboard",
      b2`
        <div class="list">
          ${dashboardFeed.length ? dashboardFeed.slice(0, 8).map((item) => this._renderFeedItem(item)) : b2`<div class="empty">Лента панели пока пуста.</div>`}
        </div>
      `,
      A,
      "feed-panel"
    );
    const recentSection = this._renderPanelCard(
      this._config.view_mode === "recent" ? this._config.title ?? "\u041F\u043E\u0441\u043B\u0435\u0434\u043D\u0438\u0435 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F" : "\u041F\u043E\u0441\u043B\u0435\u0434\u043D\u0438\u0435 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F",
      this._config.compact ? "" : "\u041F\u043E\u0441\u043B\u0435\u0434\u043D\u0438\u0435 \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0438 \u0438 \u0441\u0432\u043E\u0434\u043A\u0438",
      b2`
        <div class="list">
          ${recent.length ? recent.slice(0, this._recentLimit()).map((item) => this._renderNotification(item)) : b2`<div class="empty">Уведомлений пока нет.</div>`}
          ${this._config.compact && recent.length > this._recentLimit() ? b2`
            <details class="older-events">
              <summary>Ещё события (${recent.length - this._recentLimit()})</summary>
              <div class="list">${recent.slice(this._recentLimit()).map((item) => this._renderNotification(item))}</div>
            </details>
          ` : A}
        </div>
      `,
      A,
      "recent-panel"
    );
    if (this._config.view_mode === "general") {
      return heroCard;
    }
    if (this._config.view_mode === "policies") {
      return policySection;
    }
    if (this._config.view_mode === "policy-guide") {
      return policyGuideSection;
    }
    if (this._config.view_mode === "flows") {
      return flowsSection;
    }
    if (this._config.view_mode === "languages") {
      return languagesSection;
    }
    if (this._config.view_mode === "characters") {
      return charactersSection;
    }
    if (this._config.view_mode === "mute") {
      return muteSection;
    }
    if (this._config.view_mode === "rooms") {
      return roomsSection;
    }
    if (this._config.view_mode === "queue") {
      return queueSection;
    }
    if (this._config.view_mode === "feed") {
      return dashboardFeedSection;
    }
    if (this._config.view_mode === "recent") {
      return recentSection;
    }
    if (this._config.view_mode === "controls") {
      return b2`
        <ha-card>
          <div class="shell shell-controls">
            ${this._renderPanelCard("\u041E\u0431\u0449\u0430\u044F \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0430", "\u041E\u0433\u0440\u0430\u043D\u0438\u0447\u0435\u043D\u0438\u044F \u0438 \u043F\u043E\u0441\u043B\u0435\u0434\u043D\u044F\u044F \u043F\u0440\u043E\u0432\u0435\u0440\u043A\u0430 \u043D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438", this._renderConfigurationOverview())}
            ${channelsSection}
            ${flowsSection}
            ${languagesSection}
            ${charactersSection}
            ${muteSection}
            ${roomsSection}
          </div>
        </ha-card>
      `;
    }
    if (this._config.view_mode === "overview") {
      return b2`
        <ha-card>
          <div class="shell shell-overview">
            ${heroCard}
            ${channelsSection}
            ${flowsSection}
            ${queueSection}
            ${dashboardFeedSection}
            ${recentSection}
          </div>
        </ha-card>
      `;
    }
    return b2`
      <ha-card>
        <div class="shell">
          ${heroCard}
          ${channelsSection}
          ${policySection}
          ${policyGuideSection}
          ${flowsSection}
          ${languagesSection}
          ${charactersSection}
          ${muteSection}
          ${roomsSection}
          ${queueSection}
          ${dashboardFeedSection}
          ${recentSection}
        </div>
      </ha-card>
    `;
  }
  _renderPanelCard(title, subtitle, body, actions = A, panelClass = "") {
    return b2`
      <ha-card class="panel ${panelClass} ${this._config?.compact ? "compact-panel" : ""}">
        <div class="panel-shell">
          <div class="panel-header">
            <div>
              <h3>${title}</h3>
              ${subtitle ? b2`<span>${subtitle}</span>` : A}
            </div>
            ${actions}
          </div>
          ${body}
        </div>
      </ha-card>
    `;
  }
  _renderStat(label, value) {
    return b2`
      <div class="stat">
        <span>${label}</span>
        <strong>${value ?? "\u043D\u0435\u0442"}</strong>
      </div>
    `;
  }
  _renderFlow(flow, enabled, snoozedUntil) {
    const snoozed = Boolean(snoozedUntil && !enabled);
    return b2`
      <button class="flow ${enabled ? "enabled" : "disabled"}" @click=${() => this._toggleFlow(flow, enabled)}>
        <span class="flow-name">${this._friendlyFlowName(flow)}</span>
        <span class="flow-state">${enabled ? "\u0432\u043A\u043B\u044E\u0447\u0435\u043D\u043E" : snoozed ? `\u0434\u043E ${snoozedUntil}` : "\u0432\u044B\u043A\u043B\u044E\u0447\u0435\u043D\u043E"}</span>
      </button>
    `;
  }
  _configurationReport() {
    const current = this._statusEntity()?.attributes?.configuration_check;
    const response = this._configurationResponse;
    const report = response && response.sourceVersion === JSON.stringify(current) ? response.report : current;
    return report?.schema_version === 1 && Array.isArray(report.channels) && Array.isArray(report.restrictions) ? report : null;
  }
  _configurationRestrictions(report) {
    if (report) return report.restrictions;
    const attributes = this._statusEntity()?.attributes ?? {};
    return [
      attributes.mute_all === true && { code: "mute_all", title: "\u041E\u0431\u0449\u0435\u0435 \u0437\u0430\u0433\u043B\u0443\u0448\u0435\u043D\u0438\u0435 \u0432\u043A\u043B\u044E\u0447\u0435\u043D\u043E", detail: "\u041E\u0431\u044B\u0447\u043D\u0430\u044F \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0430 \u043E\u0433\u0440\u0430\u043D\u0438\u0447\u0435\u043D\u0430 \u043E\u0431\u0449\u0438\u043C \u0432\u044B\u043A\u043B\u044E\u0447\u0430\u0442\u0435\u043B\u0435\u043C." },
      attributes.maintenance_mode === true && { code: "maintenance", title: "\u0420\u0435\u0436\u0438\u043C \u043E\u0431\u0441\u043B\u0443\u0436\u0438\u0432\u0430\u043D\u0438\u044F", detail: "\u0414\u0435\u0439\u0441\u0442\u0432\u0443\u044E\u0442 \u043E\u0433\u0440\u0430\u043D\u0438\u0447\u0435\u043D\u0438\u044F \u0440\u0435\u0436\u0438\u043C\u0430 \u043E\u0431\u0441\u043B\u0443\u0436\u0438\u0432\u0430\u043D\u0438\u044F." },
      attributes.quiet_hours === true && { code: "quiet_hours", title: "\u0421\u0435\u0439\u0447\u0430\u0441 \u0442\u0438\u0445\u0438\u0435 \u0447\u0430\u0441\u044B", detail: "\u0414\u043E\u0441\u0442\u0430\u0432\u043A\u0430 \u0437\u0430\u0432\u0438\u0441\u0438\u0442 \u043E\u0442 \u043D\u0430\u0441\u0442\u0440\u043E\u0435\u043A \u043A\u0430\u043D\u0430\u043B\u043E\u0432 \u0438 \u043F\u0440\u0430\u0432\u0438\u043B \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0439." }
    ].filter(Boolean);
  }
  _renderConfigurationOverview() {
    const report = this._configurationReport();
    const restrictions = this._configurationRestrictions(report);
    return b2`<section class="configuration-overview" aria-label="Состояние общей доставки">
      <div class="configuration-heading"><strong>Общая доставка</strong>${this._renderConfigurationRefresh()}</div>
      ${restrictions.length ? b2`<ul class="configuration-restrictions">${restrictions.map((item) => b2`<li><strong>${item.title}</strong><p>${item.detail}</p>${item.entity_id && this.hass?.states[item.entity_id] ? b2`<button class="secondary-action restriction-action" @click=${() => this._openSetting(item.entity_id)}>Открыть настройку</button>` : A}</li>`)}</ul>` : b2`<p class="policy-hint">${report ? "\u0410\u043A\u0442\u0438\u0432\u043D\u044B\u0435 \u043E\u0431\u0449\u0438\u0435 \u043E\u0433\u0440\u0430\u043D\u0438\u0447\u0435\u043D\u0438\u044F \u043D\u0435 \u043E\u0431\u043D\u0430\u0440\u0443\u0436\u0435\u043D\u044B. \u041E\u0442\u0434\u0435\u043B\u044C\u043D\u044B\u0435 \u043F\u0440\u0430\u0432\u0438\u043B\u0430 \u0438 \u0441\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u0435 \u0443\u0441\u0442\u0440\u043E\u0439\u0441\u0442\u0432 \u043F\u043E-\u043F\u0440\u0435\u0436\u043D\u0435\u043C\u0443 \u0432\u043B\u0438\u044F\u044E\u0442 \u043D\u0430 \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0443." : "\u041F\u043E\u0434\u0440\u043E\u0431\u043D\u044B\u0439 \u043E\u0442\u0447\u0451\u0442 \u043F\u043E\u043A\u0430 \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u0435\u043D. \u041E\u0431\u0449\u0430\u044F \u0433\u043E\u0442\u043E\u0432\u043D\u043E\u0441\u0442\u044C \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0438 \u043D\u0435 \u043F\u0440\u043E\u0432\u0435\u0440\u0435\u043D\u0430."}</p>`}
      ${report ? b2`<div class="configuration-counts"><span>Каналов: ${report.summary?.total ?? report.channels.length}</span><span>Включено: ${report.summary?.enabled ?? "\u043D\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043D\u043E"}</span><span>Требуют внимания: ${report.summary?.attention ?? "\u043D\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043D\u043E"}</span><span>Проверены не полностью: ${report.summary?.not_checked ?? "\u043D\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043D\u043E"}</span></div><p class="policy-hint">Проверено: ${this._formatCheckedAt(report.checked_at)}. Это снимок настроек, а не подтверждение доставки.</p>` : A}
      ${this._configurationFeedback ? b2`<p class="policy-feedback ${this._configurationFeedback.type}" role=${this._configurationFeedback.type === "error" ? "alert" : "status"}>${this._configurationFeedback.message}</p>` : A}
    </section>`;
  }
  _openSetting(entityId) {
    if (typeof entityId !== "string" || !this.hass?.states[entityId]) return;
    this.dispatchEvent(new CustomEvent("hass-more-info", {
      detail: { entityId },
      bubbles: true,
      composed: true
    }));
  }
  _formatCheckedAt(value) {
    if (!value) return "\u0432\u0440\u0435\u043C\u044F \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D\u043E";
    const date = new Date(value);
    return Number.isNaN(date.getTime()) ? "\u0432\u0440\u0435\u043C\u044F \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D\u043E" : date.toLocaleString("ru", {
      day: "numeric",
      month: "long",
      hour: "2-digit",
      minute: "2-digit",
      timeZoneName: "short"
    });
  }
  _renderConfigurationRefresh() {
    return b2`<button class="secondary-action" ?disabled=${this._configurationBusy || Object.keys(this._controlActions).some((id) => this._controlPending(id))} @click=${() => this._refreshConfiguration()}>${this._configurationBusy ? "\u041F\u0440\u043E\u0432\u0435\u0440\u044F\u0435\u043C \u043D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438\u2026" : "\u041F\u0440\u043E\u0432\u0435\u0440\u0438\u0442\u044C \u043D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438"}</button>`;
  }
  _renderChannels() {
    const report = this._configurationReport();
    const channels = report?.channels ?? (this._statusEntity()?.attributes?.topology?.channels ?? []).map((channel) => ({ ...channel, status: "not_checked", controls: {}, settings: {}, checks: [] }));
    return this._renderPanelCard("\u041A\u0430\u043D\u0430\u043B\u044B \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0438", "\u041A\u0443\u0434\u0430 \u043D\u0430\u043F\u0440\u0430\u0432\u043B\u044F\u044E\u0442\u0441\u044F \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F \u0438 \u043A\u0430\u043A\u0438\u0435 \u043D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438 \u0434\u0435\u0439\u0441\u0442\u0432\u0443\u044E\u0442", b2`
      ${!report ? b2`<p class="policy-hint">Отчёт проверки ещё недоступен. Показана только объявленная конфигурация; управление появится, когда Herald сообщит точные сущности каналов.</p>` : A}
      <div class="channel-controls-grid">${channels.length ? channels.map((channel) => this._renderChannelControl(channel)) : b2`<p class="empty">Каналы не представлены в отчёте. Запросите проверку настроек.</p>`}</div>
      ${report?.truncated ? b2`<p class="policy-hint">Отчёт ограничен по размеру: часть каналов или проверок не показана.</p>` : A}
      ${(report?.limitations ?? ["\u0414\u043E\u0441\u0442\u0430\u0432\u043A\u0430 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0439 \u043D\u0435 \u0432\u044B\u043F\u043E\u043B\u043D\u044F\u043B\u0430\u0441\u044C \u0438 \u043D\u0435 \u043F\u043E\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043D\u0430."]).map((message) => b2`<p class="policy-hint">${message}</p>`)}
    `, A, "channel-controls-panel");
  }
  _channelControlId(channel, field) {
    const id = channel.controls?.[field];
    const domain = field === "enabled" ? "switch" : "select";
    return typeof id === "string" && id.startsWith(`${domain}.`) ? id : null;
  }
  _renderChannelControl(channel) {
    const enabledId = this._channelControlId(channel, "enabled");
    const levelId = this._channelControlId(channel, "min_level");
    const enabledEntity = this.hass?.states[enabledId];
    const levelEntity = this.hass?.states[levelId];
    const enabledKnown = this._binaryEntityKnown(enabledEntity);
    const levelKnown = this._entityUsable(levelEntity);
    const declared = channel.enabled === true ? "\u0432\u043A\u043B\u044E\u0447\u0451\u043D" : channel.enabled === false ? "\u0432\u044B\u043A\u043B\u044E\u0447\u0435\u043D" : "\u043D\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043D\u043E";
    const state = enabledKnown ? enabledEntity.state === "on" ? "\u0412\u043A\u043B\u044E\u0447\u0451\u043D" : "\u0412\u044B\u043A\u043B\u044E\u0447\u0435\u043D" : `\u041F\u043E \u043E\u0442\u0447\u0451\u0442\u0443: ${declared}`;
    const statusLabel = { configured: "\u041B\u043E\u043A\u0430\u043B\u044C\u043D\u043E \u043D\u0430\u0441\u0442\u0440\u043E\u0435\u043D", attention: "\u0422\u0440\u0435\u0431\u0443\u0435\u0442 \u0432\u043D\u0438\u043C\u0430\u043D\u0438\u044F", not_checked: "\u041F\u0440\u043E\u0432\u0435\u0440\u0435\u043D \u043D\u0435 \u043F\u043E\u043B\u043D\u043E\u0441\u0442\u044C\u044E" }[channel.status] ?? "\u041D\u0435 \u043F\u0440\u043E\u0432\u0435\u0440\u0435\u043D";
    const type = { tts: "\u0413\u043E\u043B\u043E\u0441", tts_hume: "\u0413\u043E\u043B\u043E\u0441 Hume", tv: "TV", mobile_app: "\u0422\u0435\u043B\u0435\u0444\u043E\u043D", telegram: "Telegram", dashboard: "\u041F\u0430\u043D\u0435\u043B\u044C Herald", persistent_notification: "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F Home Assistant", system_log: "\u0416\u0443\u0440\u043D\u0430\u043B" }[channel.type] ?? String(channel.type ?? "\u0422\u0438\u043F \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D");
    const quiet = { default: "\u041F\u043E \u043E\u0431\u0449\u0435\u043C\u0443 \u043F\u0440\u0430\u0432\u0438\u043B\u0443", allow: "\u0420\u0430\u0437\u0440\u0435\u0448\u0451\u043D", block: "\u0417\u0430\u043F\u0440\u0435\u0449\u0451\u043D" }[channel.quiet_hours_policy] ?? String(channel.quiet_hours_policy ?? "\u041D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D\u043E");
    return b2`<article class="channel-control-card" aria-label=${`\u041A\u0430\u043D\u0430\u043B ${this._friendlyChannelName(channel.name)}`}>
      <div class="configuration-heading"><h4>${this._friendlyChannelName(channel.name)}</h4><span class="pill ${channel.status === "attention" ? "danger" : ""}">${statusLabel}</span></div>
      <p class="policy-hint">${type} · ${channel.user ? `\u041F\u043E\u043B\u0443\u0447\u0430\u0442\u0435\u043B\u044C: ${channel.user}` : ["mobile_app", "telegram"].includes(channel.type) ? "\u0412\u043B\u0430\u0434\u0435\u043B\u0435\u0446 \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D" : "\u041E\u0431\u0449\u0438\u0439 \u043A\u0430\u043D\u0430\u043B"}${channel.rooms?.length ? ` \xB7 \u041A\u043E\u043C\u043D\u0430\u0442\u044B: ${channel.rooms.map((room) => this._friendlyRoomLabel(room)).join(", ")}` : ""}</p>
      <div class="configuration-heading"><strong>${state}</strong><button class="secondary-action" ?disabled=${!enabledKnown || this._controlPending(enabledId)} @click=${() => this._toggleSwitch(enabledId, enabledEntity?.state === "on")}>${this._controlPending(enabledId) ? "\u041E\u0436\u0438\u0434\u0430\u0435\u043C\u2026" : enabledKnown && enabledEntity.state === "on" ? "\u0412\u044B\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u043A\u0430\u043D\u0430\u043B" : "\u0412\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u043A\u0430\u043D\u0430\u043B"}</button></div>
      ${!enabledKnown ? b2`<p class="policy-hint">${enabledId ? "\u041F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0430\u0442\u0435\u043B\u044C \u043A\u0430\u043D\u0430\u043B\u0430 \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u0435\u043D \u0432 Home Assistant." : "\u0421\u0443\u0449\u043D\u043E\u0441\u0442\u044C \u0443\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u0438\u044F \u043A\u0430\u043D\u0430\u043B\u043E\u043C \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D\u0430."}</p>` : A}
      ${this._renderControlFeedback(enabledId)}
      <label class="language-card channel-level"><span>Минимальная важность</span><select aria-label=${`\u041C\u0438\u043D\u0438\u043C\u0430\u043B\u044C\u043D\u0430\u044F \u0432\u0430\u0436\u043D\u043E\u0441\u0442\u044C: ${this._friendlyChannelName(channel.name)}`} .value=${levelKnown ? levelEntity.state : ""} ?disabled=${!levelKnown || this._controlPending(levelId)} @change=${(event) => this._setSelectOption(levelId, event)}>
        ${!levelKnown ? b2`<option value="">Управление недоступно</option>` : (levelEntity.attributes.options ?? []).map((level) => b2`<option value=${level} .selected=${levelEntity.state === level}>${this._friendlyLevelLabel(level)}</option>`)}
      </select></label>
      ${!levelKnown ? b2`<p class="policy-hint">По отчёту: ${this._friendlyLevelLabel(channel.min_level ?? "unknown")}. ${levelId ? "\u0421\u0443\u0449\u043D\u043E\u0441\u0442\u044C \u043F\u043E\u0440\u043E\u0433\u0430 \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u043D\u0430." : "\u0421\u0443\u0449\u043D\u043E\u0441\u0442\u044C \u043F\u043E\u0440\u043E\u0433\u0430 \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D\u0430."}</p>` : A}
      ${this._renderControlFeedback(levelId)}
      <p class="policy-hint">В тихие часы: ${quiet}</p>
      <ul class="channel-checks">${(channel.checks ?? []).map((check) => b2`<li class=${check.status === "error" || check.status === "warning" ? "attention" : ""}>${check.message}</li>`)}</ul>
      ${Object.keys(channel.settings ?? {}).length ? b2`<details class="policy-provenance"><summary>Откуда настройки на момент проверки</summary><dl>${Object.entries(channel.settings).filter(([, setting]) => setting).map(([field, setting]) => b2`<div><dt>${field === "enabled" ? "\u0412\u043A\u043B\u044E\u0447\u0435\u043D\u0438\u0435" : "\u041C\u0438\u043D\u0438\u043C\u0430\u043B\u044C\u043D\u0430\u044F \u0432\u0430\u0436\u043D\u043E\u0441\u0442\u044C"}</dt><dd>${field === "min_level" ? this._friendlyLevelLabel(setting.value) : this._settingValue(setting.value)} · ${this._settingSource(setting.source)}${setting.inherited !== void 0 && JSON.stringify(setting.inherited) !== JSON.stringify(setting.value) ? b2`<small>Базовое значение: ${field === "min_level" ? this._friendlyLevelLabel(setting.inherited) : this._settingValue(setting.inherited)} · ${this._settingSource(setting.inherited_source)}</small>` : A}</dd></div>`)}</dl></details>` : A}
    </article>`;
  }
  _invalidateConfiguration() {
    ++this._configurationSequence;
    this._configurationResponse = null;
    this._configurationBusy = false;
    this._configurationFeedback = null;
  }
  async _refreshConfiguration() {
    if (this._configurationBusy || Object.keys(this._controlActions).some((id) => this._controlPending(id))) return;
    const token = ++this._configurationSequence;
    const sourceVersion = JSON.stringify(this._statusEntity()?.attributes?.configuration_check);
    this._configurationBusy = true;
    this._configurationFeedback = null;
    try {
      const report = await this._policyService("configuration_check", {});
      if (token !== this._configurationSequence) return;
      if (sourceVersion !== JSON.stringify(this._statusEntity()?.attributes?.configuration_check)) {
        this._configurationFeedback = { type: "success", message: "\u041F\u043E\u043B\u0443\u0447\u0435\u043D \u0431\u043E\u043B\u0435\u0435 \u0441\u0432\u0435\u0436\u0438\u0439 \u0441\u043D\u0438\u043C\u043E\u043A Home Assistant." };
        return;
      }
      if (report.schema_version !== 1 || !Array.isArray(report.channels) || !Array.isArray(report.restrictions)) throw new Error("Herald \u043D\u0435 \u0432\u0435\u0440\u043D\u0443\u043B \u043F\u043E\u0434\u0434\u0435\u0440\u0436\u0438\u0432\u0430\u0435\u043C\u044B\u0439 \u043E\u0442\u0447\u0451\u0442 \u043F\u0440\u043E\u0432\u0435\u0440\u043A\u0438. \u041E\u0431\u043D\u043E\u0432\u0438\u0442\u0435 \u0438\u043D\u0442\u0435\u0433\u0440\u0430\u0446\u0438\u044E \u0438 \u043F\u043E\u0432\u0442\u043E\u0440\u0438\u0442\u0435 \u043F\u043E\u043F\u044B\u0442\u043A\u0443.");
      this._configurationResponse = { report, sourceVersion };
      this._configurationFeedback = { type: "success", message: "\u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438 \u043F\u0440\u043E\u0432\u0435\u0440\u0435\u043D\u044B \u0431\u0435\u0437 \u043E\u0442\u043F\u0440\u0430\u0432\u043A\u0438 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0439. \u0424\u0430\u043A\u0442\u0438\u0447\u0435\u0441\u043A\u0430\u044F \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0430 \u043D\u0435 \u043F\u0440\u043E\u0432\u0435\u0440\u044F\u043B\u0430\u0441\u044C." };
    } catch (error) {
      if (token === this._configurationSequence) this._configurationFeedback = { type: "error", message: this._policyError(error) };
    } finally {
      if (token === this._configurationSequence) this._configurationBusy = false;
    }
  }
  _renderLanguage(entityId) {
    const entity = this.hass?.states[entityId];
    const known = this._entityUsable(entity);
    const options = entity?.attributes.options ?? DEFAULT_LANGUAGES;
    const label = this._friendlyEntityLabel(entityId, entity);
    return b2`
      <label class="language-card">
        <span>${label}</span>
        <select .value=${known ? entity.state : ""} ?disabled=${!known || this._controlPending(entityId)} @change=${(event) => this._setLanguage(entityId, event)}>
          ${!known ? b2`<option value="">Управление недоступно</option>` : options.map((option) => b2`<option value=${option} .selected=${entity.state === option}>${this._friendlyLanguageName(option)}</option>`)}
        </select>
        ${this._renderControlFeedback(entityId)}
      </label>
    `;
  }
  _renderCharacter(entityId) {
    const entity = this.hass?.states[entityId];
    const known = this._entityUsable(entity);
    const options = entity?.attributes.options ?? [];
    const label = this._friendlyEntityLabel(entityId, entity);
    return b2`
      <label class="language-card">
        <span>${label}</span>
        <select .value=${known ? entity.state : ""} ?disabled=${!known || this._controlPending(entityId)} @change=${(event) => this._setSelectOption(entityId, event)}>
          ${!known ? b2`<option value="">Управление недоступно</option>` : options.map((option) => b2`<option value=${option} .selected=${entity.state === option}>${this._friendlyCharacterName(option)}</option>`)}
        </select>
        ${this._renderControlFeedback(entityId)}
      </label>
    `;
  }
  _renderMute(entityId) {
    const entity = this.hass?.states[entityId];
    const known = this._binaryEntityKnown(entity);
    const muted = entity?.state === "on";
    const label = this._friendlyEntityLabel(entityId, entity);
    return b2`
      <article class="room-card ${known ? muted ? "disabled" : "enabled" : ""}">
        <div class="room-head">
          <strong>${label}</strong>
          <span class="pill">${!known ? "\u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u043D\u043E" : muted ? "\u0442\u0438\u0445\u043E" : "\u0430\u043A\u0442\u0438\u0432\u043D\u043E"}</span>
        </div>
        <div class="room-meta">
          <span>${!known ? "\u0421\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u0435 \u0437\u0430\u0433\u043B\u0443\u0448\u0435\u043D\u0438\u044F \u043D\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043D\u043E. \u041F\u0440\u043E\u0432\u0435\u0440\u044C\u0442\u0435 \u0441\u0443\u0449\u043D\u043E\u0441\u0442\u044C \u0432 Home Assistant." : muted ? "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F \u0437\u0430\u0433\u043B\u0443\u0448\u0435\u043D\u044B" : "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F \u0430\u043A\u0442\u0438\u0432\u043D\u044B"}</span>
        </div>
        <button class="room-toggle" ?disabled=${!known || this._controlPending(entityId)} @click=${() => this._toggleSwitch(entityId, muted)}>
          ${this._controlPending(entityId) ? "\u041E\u0436\u0438\u0434\u0430\u0435\u043C\u2026" : muted ? "\u0412\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u0437\u0432\u0443\u043A" : "\u0417\u0430\u0433\u043B\u0443\u0448\u0438\u0442\u044C"}
        </button>
        ${this._renderControlFeedback(entityId)}
      </article>
    `;
  }
  _renderRoom(item) {
    const sensorEntityId = item?.sensor ?? "";
    const fallbackEntityId = item?.fallback ?? "";
    const sensor = this.hass?.states[sensorEntityId];
    const fallback = this.hass?.states[fallbackEntityId];
    const roomName = item?.room ?? sensor?.attributes?.room ?? fallback?.attributes?.room ?? sensorEntityId ?? fallbackEntityId;
    const sensorOn = sensor?.state === "on";
    const sensorKnown = this._binaryEntityKnown(sensor);
    const fallbackKnown = this._binaryEntityKnown(fallback);
    const fallbackOn = fallback?.state === "on";
    const resolvedFrom = sensor?.attributes?.resolved_from;
    const resolvedFromLabel = resolvedFrom ? this._friendlyResolvedFrom(resolvedFrom) : "\u043D\u0435 \u043E\u043F\u0440\u0435\u0434\u0435\u043B\u0451\u043D";
    return b2`
      <article class="room-card ${sensorKnown ? sensorOn ? "occupied" : "idle" : ""}">
        <div class="room-head">
          <strong>${this._friendlyRoomLabel(roomName)}</strong>
          <span class="pill">${!sensorKnown ? "\u043F\u0440\u0438\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u0435 \u043D\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043D\u043E" : sensorOn ? "\u0437\u0430\u043D\u044F\u0442\u043E" : "\u0441\u0432\u043E\u0431\u043E\u0434\u043D\u043E"}</span>
        </div>
        <div class="room-meta">
          <span>Сенсор: ${this._friendlyBinaryState(sensor?.state)}</span>
          <span>Fallback: ${this._friendlyBinaryState(fallback?.state)}</span>
          <span>Источник: ${resolvedFromLabel}</span>
        </div>
        ${fallbackEntityId ? b2`
              <button class="room-toggle" ?disabled=${!fallbackKnown || this._controlPending(fallbackEntityId)} @click=${() => this._toggleSwitch(fallbackEntityId, fallbackOn)}>
                ${!fallbackKnown ? "Fallback \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u0435\u043D" : this._controlPending(fallbackEntityId) ? "\u041E\u0436\u0438\u0434\u0430\u0435\u043C\u2026" : fallbackOn ? "\u0412\u044B\u043A\u043B\u044E\u0447\u0438\u0442\u044C fallback" : "\u0412\u043A\u043B\u044E\u0447\u0438\u0442\u044C fallback"}
              </button>
            ` : A}
        ${this._renderControlFeedback(fallbackEntityId)}
      </article>
    `;
  }
  _renderNotification(item) {
    const message = String(item.message ?? "");
    const compact = this._config?.compact === true;
    if (compact) {
      const preview = message.replace(/\s+/g, " ").trim();
      return b2`
        <details class="event-entry">
          <summary>
            <ha-icon icon="mdi:bell-outline"></ha-icon>
            <span class="event-preview">
              <strong>${this._friendlyDeliveryItemTitle(item, "\u0421\u043E\u0431\u044B\u0442\u0438\u0435 \u0434\u043E\u043C\u0430")}</strong>
              ${preview ? b2`<span class="event-description">${preview.length > 110 ? `${preview.slice(0, 110)}\u2026` : preview}</span>` : A}
            </span>
            <time datetime=${String(item.timestamp ?? "")} title=${this._notificationTime(item.timestamp)}>${this._notificationTime(item.timestamp, true)}</time>
            <ha-icon class="event-chevron" icon="mdi:chevron-down"></ha-icon>
          </summary>
          <div class="event-content">
            <span class="event-date">${this._notificationTime(item.timestamp)}</span>
            <p class="event-text">${message}</p>
          </div>
        </details>
      `;
    }
    return b2`
      <article class="notification">
        <div class="notification-head">
          <strong>${this._notificationTime(item.timestamp)} · ${this._friendlyDeliveryItemTitle(item, "Herald")}</strong>
          <span class="pill">${this._friendlyLevelLabel(item.level ?? "info")}</span>
        </div>
        <p class="event-text">${message}</p>
      </article>
    `;
  }
  _recentLimit() {
    const limit = this._config?.max_items;
    return Number.isInteger(limit) && limit > 0 ? Math.min(limit, 8) : 8;
  }
  _notificationTime(timestamp, timeOnly = false) {
    if (!timestamp) return "\u0412\u0440\u0435\u043C\u044F \u043D\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043D\u043E";
    const date = new Date(timestamp);
    if (Number.isNaN(date.getTime())) return "\u0412\u0440\u0435\u043C\u044F \u043D\u0435\u0438\u0437\u0432\u0435\u0441\u0442\u043D\u043E";
    return new Intl.DateTimeFormat(this.hass?.language || "ru", {
      ...timeOnly ? {} : { day: "2-digit", month: "2-digit" },
      hour: "2-digit",
      minute: "2-digit",
      timeZone: this.hass?.config?.time_zone
    }).format(date);
  }
  _renderQueuedItem(item) {
    const channels = Array.isArray(item.channels) && item.channels.length ? item.channels.join(", ") : "\u0430\u0432\u0442\u043E";
    return b2`
      <article class="notification">
        <div class="notification-head">
          <strong>${this._friendlyDeliveryItemTitle(item, "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0435 \u0432 \u043E\u0447\u0435\u0440\u0435\u0434\u0438")}</strong>
          <span class="pill">${this._friendlyLevelLabel(item.level ?? "info")}</span>
        </div>
        <p>${String(item.message ?? "")}</p>
        <footer>
          <span>${this._formatChannels(Array.isArray(item.channels) ? item.channels : []) || channels}</span>
          <span>${String(item.enqueued_at ?? item.timestamp ?? "")}</span>
          <span>окно ${item.summary_window_seconds ?? 0} c</span>
        </footer>
      </article>
    `;
  }
  _renderFeedItem(item) {
    const channel = item.channel ?? "dashboard";
    const room = item.room ?? "n/a";
    return b2`
      <article class="notification">
        <div class="notification-head">
          <strong>${this._friendlyDeliveryItemTitle(item, "\u041B\u0435\u043D\u0442\u0430 \u043F\u0430\u043D\u0435\u043B\u0438")}</strong>
          <span class="pill">${this._friendlyLevelLabel(item.level ?? "info")}</span>
        </div>
        <p>${String(item.message ?? "")}</p>
        <footer>
          <span>${this._friendlyChannelName(channel)}</span>
          <span>${room === "n/a" ? "\u0431\u0435\u0437 \u043A\u043E\u043C\u043D\u0430\u0442\u044B" : this._friendlyRoomLabel(room)}</span>
          <span>${String(item.timestamp ?? "")}</span>
        </footer>
      </article>
    `;
  }
  _renderPolicyTable(pageData, totalItems) {
    const selected = pageData.items.find((item) => item.notification_key === this._policyExpanded);
    return b2`
      ${selected ? b2`<div class="policy-editor-container">${this._renderPolicyEditor(selected)}</div>` : A}
      <div class="policy-table-wrap">
        <table class="policy-table">
          <thead>
            <tr>
              <th>Уведомление</th>
              <th>Семейство</th>
              <th>Состояние</th>
              <th>Доставка</th>
              <th>Каналы</th>
              <th>Последнее событие</th>
              <th>Источники</th>
              <th>Действия</th>
            </tr>
          </thead>
          <tbody>
            ${pageData.items.map((item) => this._renderPolicyTableRow(item))}
          </tbody>
        </table>
      </div>
      <div class="policy-pager">
        <div class="policy-meta">
          <span>Показано ${(pageData.items ?? []).length} из ${totalItems}</span>
          <span>Страница ${pageData.page} из ${pageData.totalPages || 1}</span>
        </div>
        <div class="policy-actions">
          <button class="secondary-action" ?disabled=${pageData.page <= 1} @click=${() => this._setPolicyPage(pageData.page - 1)}>
            Назад
          </button>
          <button class="secondary-action" ?disabled=${pageData.page >= pageData.totalPages} @click=${() => this._setPolicyPage(pageData.page + 1)}>
            Дальше
          </button>
        </div>
      </div>
    `;
  }
  _renderPolicyTableRow(item) {
    item = this._policyItem(item);
    const key = String(item.notification_key ?? "");
    const effective = item.effective ?? {};
    const policy = item.policy ?? {};
    const lastEventAt = item.last_seen_at ?? item.family_last_event_at ?? "\u043D\u0435\u0442";
    const titleLabel = this._friendlyNotificationTitle(item);
    const routeLabel = this._friendlyRouteLabel(item);
    const eventLabel = this._friendlyEventLabel(item.family_last_event_code ?? "n/a");
    const isCustomized = this._policyCustomized(item);
    const expanded = this._policyExpanded === key;
    return b2`
      <tr class="policy-row ${item.active ? "is-active" : ""} ${item.active_attention ? "is-attention" : ""}">
        <td>
          <div class="policy-row-main">
            <strong>${titleLabel}</strong>
            ${item.selected_title_ru && item.selected_title_ru !== titleLabel ? b2`<div class="policy-table-subline">${item.selected_title_ru}</div>` : A}
          </div>
        </td>
        <td>
          <span class="pill">${this._friendlyFamilyLabel(item.family ?? "general")}</span>
        </td>
        <td>
          <div class="policy-status-stack">
            <span class="policy-status ${effective.enabled ? "enabled" : "disabled"}">${effective.enabled ? "\u0432\u043A\u043B" : "\u0432\u044B\u043A\u043B"}</span>
            ${item.active ? b2`<span class="pill active">активно</span>` : A}
            ${item.active_attention ? b2`<span class="pill danger">внимание</span>` : A}
            ${isCustomized ? b2`<span class="pill custom">кастом</span>` : A}
            ${item.selected_state_ru ? b2`<span class="policy-table-subline">${item.selected_state_ru}</span>` : A}
          </div>
        </td>
        <td>
          <div class="policy-row-main">
            <strong>${this._friendlyDeliveryMode(effective.delivery_mode ?? "inherit")}</strong>
            <div class="policy-table-subline">${routeLabel}</div>
          </div>
        </td>
        <td>
          <div class="policy-row-main">
            <strong>${this._policyRouteSummary(item.policy ?? {}, item.default_flow)}</strong>
            ${isCustomized ? b2`<div class="policy-table-subline">${this._policyTargetSummary(item.policy, item)}</div>` : A}
          </div>
        </td>
        <td>
          <div class="policy-row-main">
            <strong>${eventLabel}</strong>
            <div class="policy-table-subline">${lastEventAt}</div>
          </div>
        </td>
        <td>
          <div class="policy-row-main">
            <strong>${item.source_count ?? (item.source_files?.length ?? 0)}</strong>
            <div class="policy-table-subline">${this._friendlySourceCount(item.source_count ?? (item.source_files?.length ?? 0))}</div>
          </div>
        </td>
        <td>
          <div class="policy-inline-actions">
            <button class="secondary-action" @click=${() => this._togglePolicyExpanded(key)}>
              ${expanded ? "\u0421\u043A\u0440\u044B\u0442\u044C" : "\u0420\u0435\u0434\u0430\u043A\u0442\u0438\u0440\u043E\u0432\u0430\u0442\u044C"}
            </button>
            <button class="secondary-action" ?disabled=${this._busyPolicy === key} @click=${() => this._togglePolicyEnabled(item)}>
              ${effective.enabled ? "\u0412\u044B\u043A\u043B\u044E\u0447\u0438\u0442\u044C" : "\u0412\u043A\u043B\u044E\u0447\u0438\u0442\u044C \u043F\u043E \u043E\u0431\u0449\u0435\u043C\u0443 \u043F\u0440\u0430\u0432\u0438\u043B\u0443"}
            </button>
          </div>
        </td>
      </tr>
    `;
  }
  _renderPolicyEditor(item) {
    item = this._policyItem(item);
    const key = String(item.notification_key ?? "");
    const saved = this._normalizedPolicy(item.policy);
    const draft = this._policyPayload(item);
    const dirty = this._policyDirty(item);
    const busy = Boolean(this._busyPolicy);
    const feedback = this._policyFeedback[key];
    const preview = this._policyPreviews[key];
    const scenario = this._policyScenarios[key] ?? "current";
    const availableChannels = item.available_channels ?? [];
    const userOptions = this._policyTargetOptions(item, "users", draft.users ?? []);
    const roomOptions = this._policyTargetOptions(item, "rooms", draft.target_room ? [draft.target_room] : []);
    const last = item.last_decision;
    return b2`
      <article class="policy-card policy-card-editor">
        <div class="policy-editor-heading">
          <div>
            <h4 tabindex="-1">${this._friendlyNotificationTitle(item)}</h4>
            <p class="policy-hint">Сохранено: ${this._policyRouteSummary(saved, item.default_flow)}</p>
            <p class="policy-hint policy-saved-targets">${this._policyTargetSummary(saved, item)}</p>
          </div>
          <span class="pill ${dirty ? "custom" : "active"}">${dirty ? "\u0415\u0441\u0442\u044C \u0438\u0437\u043C\u0435\u043D\u0435\u043D\u0438\u044F" : "\u0421\u043E\u0445\u0440\u0430\u043D\u0451\u043D\u043D\u043E\u0435 \u043F\u0440\u0430\u0432\u0438\u043B\u043E"}</span>
        </div>
        ${last ? b2`<div class="policy-last-decision"><strong>Последнее решение</strong><p>${last.summary ?? last.reason ?? "\u041D\u0435\u0442 \u043E\u0431\u044A\u044F\u0441\u043D\u0435\u043D\u0438\u044F"}</p>${last.at ? b2`<small>${last.at}</small>` : A}</div>` : A}
        <label class="policy-enabled"><input type="checkbox" .checked=${draft.enabled && draft.delivery_mode !== "disabled"} @change=${(event) => this._setPolicyDraft(key, "enabled", event.target.checked, event.target.checked && draft.delivery_mode === "disabled" ? { delivery_mode: "inherit" } : {})} /> Доставлять это уведомление</label>
        <label class="language-card policy-field">
          <span>Как доставлять</span>
          <select aria-label="Как доставлять" .value=${draft.delivery_mode} @change=${(event) => this._setPolicyDraft(key, "delivery_mode", event.target.value)}>
            ${["inherit", "disabled", "text_only", "voice_only", "push_only", "custom"].map((mode) => b2`<option value=${mode} .selected=${draft.delivery_mode === mode}>${this._friendlyDeliveryMode(mode)}</option>`)}
          </select>
        </label>
        <p class="policy-rule-summary">${this._policyRouteSummary(draft, item.default_flow)}</p>
        ${draft.delivery_mode === "inherit" ? b2`<p class="policy-hint">Маршрут определится общими настройками, потоком и присутствием. Проверка ниже покажет результат для выбранной ситуации.</p>` : A}
        ${draft.delivery_mode === "custom" ? b2`
          <fieldset class="policy-channel-fieldset"><legend>Выбранные каналы</legend>
            <div class="policy-channel-grid">
              ${availableChannels.map((channel) => b2`<button type="button" class="policy-channel ${draft.channels.includes(channel) ? "selected" : ""}" aria-pressed=${draft.channels.includes(channel)} @click=${() => this._togglePolicyDraftChannel(key, channel, item)}>${this._friendlyChannelName(channel)}</button>`)}
            </div>
            ${!availableChannels.length ? b2`<p class="policy-hint">Каналы не найдены. Проверьте настройки устройств.</p>` : A}
          </fieldset>` : A}
        <div class="policy-target-grid">
          <section class="policy-rule-section" aria-label="Кому доставлять">
            <h5>Кому</h5>
            <label class="language-card policy-field"><span>Получатели личных сообщений</span>
              <select aria-label="Получатели личных сообщений" .value=${draft.users === null ? "inherit" : "selected"} @change=${(event) => this._setPolicyDraft(key, "users", event.target.value === "inherit" ? null : [])}>
                <option value="inherit">По общему правилу</option><option value="selected">Выбрать получателей</option>
              </select>
            </label>
            ${draft.users !== null ? b2`<div class="policy-channel-grid policy-user-options" role="group" aria-label="Выбранные получатели">
              ${userOptions.map((option) => b2`<button type="button" class="policy-channel ${draft.users.includes(option.value) ? "selected" : ""}" aria-pressed=${draft.users.includes(option.value)} @click=${() => this._togglePolicyDraftUser(key, option.value, item)}>${option.label}</button>`)}
            </div>${!draft.users.length ? b2`<p class="policy-hint policy-empty-recipients">Получатели не выбраны — доставки не будет.</p>` : A}` : A}
            <p class="policy-hint">Выбор ограничивает личные каналы. При доставке общие каналы панели и журнала остаются общими. Локальный голос доступен только для подходящих получателей дома; его могут услышать и другие люди.</p>
          </section>
          <section class="policy-rule-section" aria-label="Где доставлять">
            <h5>Где</h5>
            <label class="language-card policy-field"><span>Комната для голоса и TV</span>
              <select aria-label="Комната для голоса и TV" .value=${draft.target_room ?? ""} @change=${(event) => this._setPolicyDraft(key, "target_room", event.target.value || null)}>
                <option value="" .selected=${draft.target_room === null}>Автоматически по общему правилу</option>
                ${roomOptions.map((option) => b2`<option value=${option.value} .selected=${draft.target_room === option.value}>${option.label}</option>`)}
              </select>
            </label>
            <p class="policy-hint">Выбранная комната используется строго для голоса и TV, без перехода в другую комнату. Личные каналы получателей не меняются.</p>
          </section>
        </div>
        <section class="policy-rule-section" aria-label="Когда доставлять">
          <h5>Когда</h5>
          <div class="policy-target-grid">
            <label class="language-card policy-field"><span>Присутствие дома</span>
              <select aria-label="Присутствие дома" .value=${draft.presence} @change=${(event) => this._setPolicyDraft(key, "presence", event.target.value)}>
                <option value="any">При любом присутствии</option><option value="someone_home">Только когда кто-то дома</option><option value="nobody_home">Только когда никого дома</option>
              </select>
            </label>
            <label class="language-card policy-field"><span>В тихие часы</span>
              <select aria-label="В тихие часы" .value=${draft.quiet_hours} @change=${(event) => this._setPolicyDraft(key, "quiet_hours", event.target.value)}>
                <option value="inherit">По общему правилу</option><option value="text_only">Только текст</option><option value="mute">Не доставлять</option>
              </select>
            </label>
          </div>
          <p class="policy-hint">Условия проверяются в момент события. Отложенная отправка и расписание здесь не задаются.</p>
        </section>
        <p class="policy-draft-targets"><strong>${dirty ? "\u0427\u0435\u0440\u043D\u043E\u0432\u0438\u043A" : "\u041F\u0440\u0430\u0432\u0438\u043B\u043E"}:</strong> ${this._policyTargetSummary(draft, item)}</p>
        <details class="policy-advanced">
          <summary>Дополнительно: важность и интервал</summary>
          <div class="policy-grid policy-grid-advanced">
            <label class="language-card policy-field"><span>Важность вместо уровня события</span>
              <select .value=${draft.level_override} @change=${(event) => this._setPolicyDraft(key, "level_override", event.target.value)}>
                ${["", "debug", "info", "notice", "warning", "critical", "security", "ai", "system"].map((level) => b2`<option value=${level}>${level ? this._friendlyLevelLabel(level) : "\u0423\u0440\u043E\u0432\u0435\u043D\u044C \u0441\u0430\u043C\u043E\u0433\u043E \u0441\u043E\u0431\u044B\u0442\u0438\u044F"}</option>`)}
              </select>
            </label>
            <label class="language-card policy-field"><span>Минимальный интервал, секунд</span>
              <input type="number" min="0" max="86400" step="1" .value=${String(draft.cooldown_override ?? "")} placeholder="По общему правилу" @input=${(event) => this._setPolicyDraft(key, "cooldown_override", event.target.value)} />
            </label>
          </div>
          <p class="policy-hint">Пустой интервал использует настройку потока; 0 отключает это ограничение для уведомления.</p>
        </details>
        <label class="language-card policy-field"><span>Заметка к правилу</span><input .value=${draft.notes} placeholder="Почему выбрана эта настройка" @input=${(event) => this._setPolicyDraft(key, "notes", event.target.value)} /></label>
        <section class="policy-preview" aria-label="Проверка доставки">
          <div class="policy-preview-heading"><strong>Проверка без отправки</strong><span class="policy-hint">${dirty ? "\u0418\u0441\u043F\u043E\u043B\u044C\u0437\u0443\u0435\u0442\u0441\u044F \u043D\u0435\u0441\u043E\u0445\u0440\u0430\u043D\u0451\u043D\u043D\u044B\u0439 \u0447\u0435\u0440\u043D\u043E\u0432\u0438\u043A" : "\u0418\u0441\u043F\u043E\u043B\u044C\u0437\u0443\u0435\u0442\u0441\u044F \u0441\u043E\u0445\u0440\u0430\u043D\u0451\u043D\u043D\u043E\u0435 \u043F\u0440\u0430\u0432\u0438\u043B\u043E"}</span></div>
          <div class="policy-preview-controls">
            <label>Ситуация<select aria-label="Ситуация" .value=${scenario} @change=${(event) => this._setPolicyScenario(key, event.target.value)}>
              <option value="current">Сейчас</option><option value="quiet_hours">Тихие часы</option><option value="away">Никого дома</option>
            </select></label>
            <button class="secondary-action" ?disabled=${preview?.loading} @click=${() => this._previewPolicy(item)}>${preview?.loading ? "\u041F\u0440\u043E\u0432\u0435\u0440\u044F\u0435\u043C\u2026" : "\u041F\u0440\u043E\u0432\u0435\u0440\u0438\u0442\u044C \u0431\u0435\u0437 \u043E\u0442\u043F\u0440\u0430\u0432\u043A\u0438"}</button>
          </div>
          <p class="policy-hint">Уведомления и команды устройствам не отправляются. ${scenario === "quiet_hours" ? "\u041C\u043E\u0434\u0435\u043B\u0438\u0440\u0443\u0435\u0442\u0441\u044F \u043F\u0440\u0430\u0432\u0438\u043B\u043E \u0442\u0438\u0445\u0438\u0445 \u0447\u0430\u0441\u043E\u0432; \u0432\u0440\u0435\u043C\u044F \u0438 \u0443\u0441\u043B\u043E\u0432\u0438\u044F \u0430\u0432\u0442\u043E\u043C\u0430\u0442\u0438\u0437\u0430\u0446\u0438\u0439 \u043E\u0441\u0442\u0430\u044E\u0442\u0441\u044F \u0442\u0435\u043A\u0443\u0449\u0438\u043C\u0438." : scenario === "away" ? "\u041C\u043E\u0434\u0435\u043B\u0438\u0440\u0443\u0435\u0442\u0441\u044F \u043E\u0442\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u0435 \u043B\u044E\u0434\u0435\u0439 \u0434\u043E\u043C\u0430; \u0441\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u044F \u0443\u0441\u0442\u0440\u043E\u0439\u0441\u0442\u0432 \u0438 \u0432\u0440\u0435\u043C\u044F \u043E\u0441\u0442\u0430\u044E\u0442\u0441\u044F \u0442\u0435\u043A\u0443\u0449\u0438\u043C\u0438." : "\u0418\u0441\u043F\u043E\u043B\u044C\u0437\u0443\u044E\u0442\u0441\u044F \u0442\u0435\u043A\u0443\u0449\u0438\u0435 \u0441\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u044F \u0443\u0441\u0442\u0440\u043E\u0439\u0441\u0442\u0432 \u0438 \u0432\u0440\u0435\u043C\u044F."}</p>
          ${preview?.error ? b2`<p class="policy-feedback error" role="alert">${preview.error}</p>` : A}
          ${preview?.result ? this._renderPolicyExplanation(preview.result) : A}
        </section>
        ${feedback ? b2`<p class="policy-feedback ${feedback.type}" role=${feedback.type === "error" ? "alert" : "status"}>${feedback.message}</p>` : A}
        <div class="policy-actions">
          <button class="secondary-action primary-action" ?disabled=${busy || !dirty} @click=${() => this._savePolicy(item)}>${this._busyPolicy === key ? "\u0421\u043E\u0445\u0440\u0430\u043D\u044F\u0435\u043C\u2026" : "\u0421\u043E\u0445\u0440\u0430\u043D\u0438\u0442\u044C \u0438\u0437\u043C\u0435\u043D\u0435\u043D\u0438\u044F"}</button>
          <button class="secondary-action" ?disabled=${busy || !dirty} @click=${() => this._discardPolicyDraft(key)}>Отменить изменения</button>
          <button class="secondary-action" ?disabled=${busy} @click=${() => this._resetPolicy(item)}>Вернуть общее правило</button>
        </div>
      </article>
    `;
  }
  _renderPolicyExplanation(result) {
    const explanation = result.explanation;
    return b2`<div class="policy-explanation" aria-live="polite">
      <strong>${explanation.summary}</strong>
      <p>${explanation.channels?.length ? `\u041A\u0430\u043D\u0430\u043B\u044B: ${this._formatChannels(explanation.channels)}` : "\u0414\u043E\u0441\u0442\u0430\u0432\u043A\u0430 \u043D\u0435 \u0437\u0430\u043F\u043B\u0430\u043D\u0438\u0440\u043E\u0432\u0430\u043D\u0430"}</p>
      ${explanation.steps?.length ? b2`<ol>${explanation.steps.map((step) => b2`<li><strong>${step.label}</strong> ${step.detail}</li>`)}</ol>` : A}
      ${[.../* @__PURE__ */ new Set([...explanation.warnings ?? [], ...result.warnings ?? []])].map((warning) => b2`<p class="policy-hint">${warning}</p>`)}
      ${Object.keys(result.effective_settings ?? {}).length ? b2`<details class="policy-provenance"><summary>Откуда настройки</summary><dl>${Object.entries(result.effective_settings).map(([key, setting]) => b2`<div><dt>${this._settingLabel(key)}</dt><dd>${this._settingValue(setting.value)} · ${this._settingSource(setting.source)}${setting.inherited !== void 0 && JSON.stringify(setting.inherited) !== JSON.stringify(setting.value) ? b2`<small>Базовое значение: ${this._settingValue(setting.inherited)} · ${this._settingSource(setting.inherited_source)}</small>` : A}</dd></div>`)}</dl></details>` : A}
      <small>Это проверка черновика без отправки. Реальный результат может измениться вместе с состоянием дома.</small>
    </div>`;
  }
  _settingSource(source) {
    return { options: "\u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438 \u0438\u043D\u0442\u0435\u0433\u0440\u0430\u0446\u0438\u0438", runtime: "\u0420\u0443\u0447\u043D\u043E\u0435 \u0438\u0437\u043C\u0435\u043D\u0435\u043D\u0438\u0435", restored: "\u0421\u043E\u0445\u0440\u0430\u043D\u0451\u043D\u043D\u043E\u0435 \u043F\u0435\u0440\u0435\u043E\u043F\u0440\u0435\u0434\u0435\u043B\u0435\u043D\u0438\u0435", default: "\u041F\u043E \u0443\u043C\u043E\u043B\u0447\u0430\u043D\u0438\u044E", yaml: "YAML", entry: "\u041D\u0430\u0447\u0430\u043B\u044C\u043D\u0430\u044F \u043D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0430", legacy: "\u041F\u0440\u0435\u0436\u043D\u044F\u044F \u043D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0430" }[source] ?? "\u0418\u0441\u0442\u043E\u0447\u043D\u0438\u043A \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D";
  }
  _settingValue(value) {
    if (value === true) return "\u0412\u043A\u043B\u044E\u0447\u0435\u043D\u043E";
    if (value === false) return "\u0412\u044B\u043A\u043B\u044E\u0447\u0435\u043D\u043E";
    return value == null ? "\u041D\u0435 \u0437\u0430\u0434\u0430\u043D\u043E" : String(value);
  }
  _settingLabel(key) {
    const [kind, name] = key.split(":", 2);
    const label = { flow_enabled: "\u041F\u043E\u0442\u043E\u043A", flow_cooldown: "\u0418\u043D\u0442\u0435\u0440\u0432\u0430\u043B \u043F\u043E\u0442\u043E\u043A\u0430, \u0441", flow_dedup_window: "\u041F\u043E\u0432\u0442\u043E\u0440\u044B \u043F\u043E\u0442\u043E\u043A\u0430, \u0441", channel_enabled: "\u041A\u0430\u043D\u0430\u043B", channel_min_level: "\u041F\u043E\u0440\u043E\u0433 \u0432\u0430\u0436\u043D\u043E\u0441\u0442\u0438 \u043A\u0430\u043D\u0430\u043B\u0430", maintenance_min_level: "\u041F\u043E\u0440\u043E\u0433 \u0440\u0435\u0436\u0438\u043C\u0430 \u043E\u0431\u0441\u043B\u0443\u0436\u0438\u0432\u0430\u043D\u0438\u044F" }[kind] ?? kind;
    return name ? `${label}: ${kind.startsWith("flow_") ? this._friendlyFlowName(name) : this._friendlyChannelName(name)}` : label;
  }
  async _toggleFlow(flow, enabled) {
    if (!this.hass || this._busyFlow === flow) {
      return;
    }
    this._busyFlow = flow;
    try {
      await this.hass.callService("herald", "set_flow_state", {
        flow,
        enabled: !enabled
      });
    } finally {
      this._busyFlow = "";
    }
  }
  async _setLanguage(entityId, event) {
    if (!this.hass) {
      return;
    }
    await this._setSelectOption(entityId, event);
  }
  async _setSelectOption(entityId, event) {
    const entity = this.hass?.states[entityId];
    const option = event.target.value;
    event.target.value = this._entityUsable(entity) ? entity.state : "";
    if (!entityId?.startsWith("select.") || !this._entityUsable(entity) || !(entity.attributes.options ?? []).includes(option)) {
      this._controlActions = { ...this._controlActions, [entityId]: { phase: "error", message: "\u0421\u0443\u0449\u043D\u043E\u0441\u0442\u044C \u0438\u043B\u0438 \u0432\u044B\u0431\u0440\u0430\u043D\u043D\u043E\u0435 \u0437\u043D\u0430\u0447\u0435\u043D\u0438\u0435 \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u043D\u044B \u0432 Home Assistant." } };
      return;
    }
    await this._runControlAction(entityId, option, "select", "select_option", { entity_id: entityId, option });
  }
  async _toggleSwitch(entityId, enabled) {
    const entity = this.hass?.states[entityId];
    if (!entityId?.startsWith("switch.") || !this._binaryEntityKnown(entity)) {
      this._controlActions = { ...this._controlActions, [entityId]: { phase: "error", message: "\u041F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0430\u0442\u0435\u043B\u044C \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u0435\u043D \u0432 Home Assistant." } };
      return;
    }
    const next = entity.state === "on" ? "off" : "on";
    await this._runControlAction(entityId, next, "switch", next === "on" ? "turn_on" : "turn_off", { entity_id: entityId });
  }
  _entityUsable(entity) {
    return Boolean(entity && entity.state != null && !["", "unknown", "unavailable"].includes(entity.state));
  }
  _binaryEntityKnown(entity) {
    return entity?.state === "on" || entity?.state === "off";
  }
  _controlPending(entityId) {
    return ["sending", "awaiting"].includes(this._controlActions[entityId]?.phase);
  }
  _renderControlFeedback(entityId) {
    const action = this._controlActions[entityId];
    if (!action) return A;
    const message = action.message ?? { sending: "\u0421\u043E\u0445\u0440\u0430\u043D\u044F\u0435\u043C\u2026", awaiting: "\u041A\u043E\u043C\u0430\u043D\u0434\u0430 \u043F\u0440\u0438\u043D\u044F\u0442\u0430. \u041E\u0436\u0438\u0434\u0430\u0435\u043C \u043D\u043E\u0432\u043E\u0435 \u0441\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u0435 Home Assistant.", success: "\u0418\u0437\u043C\u0435\u043D\u0435\u043D\u0438\u0435 \u043F\u043E\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043D\u043E Home Assistant." }[action.phase];
    return b2`<p class="policy-feedback ${action.phase === "error" ? "error" : "success"}" role=${action.phase === "error" ? "alert" : "status"}>${message}</p>`;
  }
  _clearControlActions() {
    for (const timer of this._controlTimers.values()) clearTimeout(timer);
    this._controlTimers.clear();
    this._controlActions = {};
  }
  _finishControlAction(entityId, token, phase, message) {
    if (this._controlActions[entityId]?.token !== token) return;
    clearTimeout(this._controlTimers.get(entityId));
    this._controlTimers.delete(entityId);
    this._controlActions = { ...this._controlActions, [entityId]: { ...this._controlActions[entityId], phase, message } };
  }
  _reconcileControlActions() {
    for (const [entityId, action] of Object.entries(this._controlActions)) {
      const state = this.hass?.states[entityId]?.state;
      const matches = state === action.expected || entityId.startsWith("number.") && this._entityUsable(this.hass?.states[entityId]) && Number(state) === Number(action.expected);
      if (action.phase === "awaiting" && matches) this._finishControlAction(entityId, action.token, "success");
    }
  }
  _expireControlAction(entityId, token) {
    if (!this._controlPending(entityId)) return;
    this._finishControlAction(entityId, token, "error", "\u041F\u043E\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043D\u0438\u0435 \u043E\u0442 Home Assistant \u043D\u0435 \u043F\u043E\u043B\u0443\u0447\u0435\u043D\u043E. \u041F\u043E\u043A\u0430\u0437\u0430\u043D\u043E \u043F\u043E\u0441\u043B\u0435\u0434\u043D\u0435\u0435 \u0438\u0437\u0432\u0435\u0441\u0442\u043D\u043E\u0435 \u0441\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u0435; \u043F\u0440\u043E\u0432\u0435\u0440\u044C\u0442\u0435 \u0435\u0433\u043E \u043F\u0435\u0440\u0435\u0434 \u043F\u043E\u0432\u0442\u043E\u0440\u043E\u043C.");
  }
  async _runControlAction(entityId, expected, domain, service, data) {
    if (!this.hass || this._controlPending(entityId) || this.hass.states[entityId]?.state === expected) return;
    const token = ++this._controlSequence;
    this._invalidateConfiguration();
    this._configurationFeedback = { type: "success", message: "\u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438 \u043C\u0435\u043D\u044F\u044E\u0442\u0441\u044F. \u041F\u043E\u0441\u043B\u0435 \u043F\u043E\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043D\u0438\u044F \u043E\u0431\u043D\u043E\u0432\u0438\u0442\u0435 \u043F\u0440\u043E\u0432\u0435\u0440\u043A\u0443." };
    this._controlActions = { ...this._controlActions, [entityId]: { token, phase: "sending", expected } };
    const timer = setTimeout(() => this._expireControlAction(entityId, token), 1e4);
    timer?.unref?.();
    this._controlTimers.set(entityId, timer);
    try {
      await this.hass.callService(domain, service, data);
      if (this._controlActions[entityId]?.token !== token || !this._controlPending(entityId)) return;
      this._controlActions = { ...this._controlActions, [entityId]: { token, phase: "awaiting", expected } };
      this._reconcileControlActions();
    } catch (error) {
      if (this._controlPending(entityId)) this._finishControlAction(entityId, token, "error", this._policyError(error));
    }
  }
  _policyDraftValue(notificationKey, field, fallback) {
    return this._policyDrafts?.[notificationKey]?.[field] ?? fallback;
  }
  _policyDraftChannels(notificationKey, item) {
    return this._policyPayload(item).channels;
  }
  _setPolicyDraft(notificationKey, field, value, relatedFields = {}) {
    this._policyDrafts = { ...this._policyDrafts, [notificationKey]: { ...this._policyDrafts[notificationKey] ?? {}, ...relatedFields, [field]: value } };
    this._policyRevisions[notificationKey] = (this._policyRevisions[notificationKey] ?? 0) + 1;
    this._clearPolicyPreview(notificationKey);
    this._policyFeedback = { ...this._policyFeedback, [notificationKey]: void 0 };
  }
  _togglePolicyDraftChannel(notificationKey, channel, item) {
    const current = this._policyDraftChannels(notificationKey, item);
    const next = current.includes(channel) ? current.filter((entry) => entry !== channel) : [...current, channel];
    this._setPolicyDraft(notificationKey, "channels", next);
  }
  _togglePolicyDraftUser(notificationKey, user, item) {
    const current = this._policyPayload(item).users ?? [];
    this._setPolicyDraft(notificationKey, "users", current.includes(user) ? current.filter((value) => value !== user) : [...current, user]);
  }
  _policyTargetOptions(item, kind, selected = []) {
    const registry = this._statusEntity()?.attributes?.notification_registry ?? {};
    const options = item[`available_${kind}`] ?? registry[kind === "users" ? "user_options" : "room_options"] ?? [];
    const known = new Map(options.filter((option) => typeof option?.value === "string" && option.value).map((option) => [option.value, { value: option.value, label: String(option.label ?? (kind === "rooms" ? this._friendlyRoomLabel(option.value) : option.value)) }]));
    for (const value of selected) if (!known.has(value)) known.set(value, { value, label: `${value} (\u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u043D\u043E)` });
    return [...known.values()];
  }
  _policyTargetSummary(policy, item) {
    const normalized = this._normalizedPolicy(policy);
    const users = normalized.users === null ? "\u041F\u043E\u043B\u0443\u0447\u0430\u0442\u0435\u043B\u0438 \u043F\u043E \u043E\u0431\u0449\u0435\u043C\u0443 \u043F\u0440\u0430\u0432\u0438\u043B\u0443" : normalized.users.length ? `\u041F\u043E\u043B\u0443\u0447\u0430\u0442\u0435\u043B\u0438: ${this._policyTargetOptions(item, "users", normalized.users).filter((option) => normalized.users.includes(option.value)).map((option) => option.label).join(", ")}` : "\u041F\u043E\u043B\u0443\u0447\u0430\u0442\u0435\u043B\u0438 \u043D\u0435 \u0432\u044B\u0431\u0440\u0430\u043D\u044B \u2014 \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0438 \u043D\u0435 \u0431\u0443\u0434\u0435\u0442";
    const room = normalized.target_room ? `\u0413\u043E\u043B\u043E\u0441 \u0438 TV: ${this._policyTargetOptions(item, "rooms", [normalized.target_room]).find((option) => option.value === normalized.target_room).label}` : "\u041A\u043E\u043C\u043D\u0430\u0442\u0430 \u0430\u0432\u0442\u043E\u043C\u0430\u0442\u0438\u0447\u0435\u0441\u043A\u0438";
    const presence = { any: "\u041F\u0440\u0438 \u043B\u044E\u0431\u043E\u043C \u043F\u0440\u0438\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u0438", someone_home: "\u0422\u043E\u043B\u044C\u043A\u043E \u043A\u043E\u0433\u0434\u0430 \u043A\u0442\u043E-\u0442\u043E \u0434\u043E\u043C\u0430", nobody_home: "\u0422\u043E\u043B\u044C\u043A\u043E \u043A\u043E\u0433\u0434\u0430 \u043D\u0438\u043A\u043E\u0433\u043E \u0434\u043E\u043C\u0430" }[normalized.presence] ?? normalized.presence;
    const quiet = { inherit: "\u0422\u0438\u0445\u0438\u0435 \u0447\u0430\u0441\u044B \u043F\u043E \u043E\u0431\u0449\u0435\u043C\u0443 \u043F\u0440\u0430\u0432\u0438\u043B\u0443", text_only: "\u0412 \u0442\u0438\u0445\u0438\u0435 \u0447\u0430\u0441\u044B \u0442\u043E\u043B\u044C\u043A\u043E \u0442\u0435\u043A\u0441\u0442", mute: "\u0412 \u0442\u0438\u0445\u0438\u0435 \u0447\u0430\u0441\u044B \u0431\u0435\u0437 \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0438" }[normalized.quiet_hours] ?? normalized.quiet_hours;
    return [users, room, presence, quiet].join(" \xB7 ");
  }
  _policyCustomized(item) {
    const policy = this._normalizedPolicy(item.policy);
    return !policy.enabled || policy.delivery_mode !== "inherit" || Boolean(policy.level_override) || policy.cooldown_override !== "" || Boolean(policy.notes) || policy.users !== null || policy.target_room !== null || policy.presence !== "any" || policy.quiet_hours !== "inherit";
  }
  _friendlyFlowName(flow) {
    const labels = {
      security_alerts: "\u0411\u0435\u0437\u043E\u043F\u0430\u0441\u043D\u043E\u0441\u0442\u044C",
      system_events: "\u0421\u0438\u0441\u0442\u0435\u043C\u043D\u044B\u0435 \u0441\u043E\u0431\u044B\u0442\u0438\u044F",
      device_alerts: "\u0423\u0441\u0442\u0440\u043E\u0439\u0441\u0442\u0432\u0430",
      ai_events: "\u0418\u0418-\u0441\u043E\u0431\u044B\u0442\u0438\u044F",
      energy_events: "\u042D\u043D\u0435\u0440\u0433\u0438\u044F",
      camera_alerts: "\u041A\u0430\u043C\u0435\u0440\u044B",
      timer_notifications: "\u0422\u0430\u0439\u043C\u0435\u0440\u044B"
    };
    return labels[flow] ?? this._humanizeCode(flow);
  }
  _friendlyLevelLabel(level) {
    const labels = {
      debug: "\u043E\u0442\u043B\u0430\u0434\u043A\u0430",
      info: "\u0438\u043D\u0444\u043E",
      notice: "\u043E\u0431\u044B\u0447\u043D\u043E\u0435",
      warning: "\u0432\u0430\u0436\u043D\u043E\u0435",
      critical: "\u043A\u0440\u0438\u0442\u0438\u0447\u043D\u043E\u0435",
      security: "\u0431\u0435\u0437\u043E\u043F\u0430\u0441\u043D\u043E\u0441\u0442\u044C",
      ai: "\u0418\u0418",
      system: "\u0441\u0438\u0441\u0442\u0435\u043C\u0430"
    };
    return labels[level] ?? this._humanizeCode(level);
  }
  _friendlyChannelName(channel) {
    const labels = {
      system_log_default: "\u0421\u0438\u0441\u0442\u0435\u043C\u043D\u044B\u0439 \u043B\u043E\u0433",
      persistent_default: "\u041F\u043E\u0441\u0442\u043E\u044F\u043D\u043D\u044B\u0435 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F",
      telegram_default: "Telegram",
      voice_auto: "\u0413\u043E\u043B\u043E\u0441: \u0430\u0432\u0442\u043E",
      dashboard_default: "\u041B\u0435\u043D\u0442\u0430 Herald",
      push_default: "Push",
      tv_default: "TV"
    };
    return labels[channel] ?? this._humanizeCode(channel);
  }
  _friendlyChannelFamilyLabel(value) {
    const labels = {
      voice: "\u0413\u043E\u043B\u043E\u0441",
      push: "Push",
      tv: "TV",
      dashboard: "\u041F\u0430\u043D\u0435\u043B\u044C",
      persistent: "\u041F\u043E\u0441\u0442\u043E\u044F\u043D\u043D\u044B\u0435",
      system_log: "\u0421\u0438\u0441\u0442\u0435\u043C\u043D\u044B\u0439 \u043B\u043E\u0433",
      mobile_app: "\u041C\u043E\u0431\u0438\u043B\u044C\u043D\u044B\u0435"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _friendlyFamilyLabel(value) {
    const labels = {
      general: "\u041E\u0431\u0449\u0435\u0435",
      ai: "\u0418\u0418",
      ai_foundation: "\u0411\u0430\u0437\u043E\u0432\u044B\u0439 \u0418\u0418",
      energy: "\u042D\u043D\u0435\u0440\u0433\u0438\u044F",
      energy_policy: "\u0422\u0430\u0440\u0438\u0444\u044B \u0438 \u0431\u044E\u0434\u0436\u0435\u0442",
      energy_runtime: "\u042D\u043D\u0435\u0440\u0433\u043E\u0441\u0438\u0433\u043D\u0430\u043B\u044B",
      reports: "\u0411\u0440\u0438\u0444\u0438\u043D\u0433\u0438 \u0438 \u043E\u0442\u0447\u0435\u0442\u044B",
      system: "\u0421\u0438\u0441\u0442\u0435\u043C\u0430",
      security: "\u0411\u0435\u0437\u043E\u043F\u0430\u0441\u043D\u043E\u0441\u0442\u044C",
      recovery: "\u0412\u043E\u0441\u0441\u0442\u0430\u043D\u043E\u0432\u043B\u0435\u043D\u0438\u0435",
      recovery_ops: "\u0412\u043E\u0441\u0441\u0442\u0430\u043D\u043E\u0432\u043B\u0435\u043D\u0438\u0435",
      timer: "\u0422\u0430\u0439\u043C\u0435\u0440",
      guests: "\u0413\u043E\u0441\u0442\u0438",
      adult_content: "18+",
      environment: "\u042D\u043A\u043E\u043B\u043E\u0433\u0438\u044F",
      geo: "\u0413\u0435\u043E",
      washer: "\u0421\u0442\u0438\u0440\u0430\u043B\u043A\u0430",
      copilot: "Copilot",
      home_mode: "\u0420\u0435\u0436\u0438\u043C \u0434\u043E\u043C\u0430",
      device_ops: "\u041E\u043F\u0435\u0440\u0430\u0446\u0438\u0438 \u0443\u0441\u0442\u0440\u043E\u0439\u0441\u0442\u0432",
      manual_lights: "\u0420\u0443\u0447\u043D\u043E\u0439 \u0441\u0432\u0435\u0442",
      household_power: "\u0424\u043E\u043D\u043E\u0432\u0430\u044F \u043D\u0430\u0433\u0440\u0443\u0437\u043A\u0430",
      tts: "\u041E\u0437\u0432\u0443\u0447\u043A\u0430",
      alarm_clock: "\u0411\u0443\u0434\u0438\u043B\u044C\u043D\u0438\u043A",
      ev_dispatcher: "EV-\u0434\u0438\u0441\u043F\u0435\u0442\u0447\u0435\u0440",
      camera: "\u041A\u0430\u043C\u0435\u0440\u044B"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _friendlyDeliveryMode(value) {
    const labels = {
      inherit: "\u041F\u043E \u043E\u0431\u0449\u0435\u043C\u0443 \u043F\u0440\u0430\u0432\u0438\u043B\u0443",
      disabled: "\u041E\u0442\u043A\u043B\u044E\u0447\u0438\u0442\u044C",
      text_only: "\u0422\u043E\u043B\u044C\u043A\u043E \u0442\u0435\u043A\u0441\u0442",
      voice_only: "\u0422\u043E\u043B\u044C\u043A\u043E \u0433\u043E\u043B\u043E\u0441",
      push_only: "\u0422\u043E\u043B\u044C\u043A\u043E push",
      custom: "\u0412\u044B\u0431\u0440\u0430\u0442\u044C \u043A\u0430\u043D\u0430\u043B\u044B"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _friendlyEntityLabel(entityId, entity) {
    const rawName = String(entity?.attributes?.friendly_name ?? "").trim();
    if (rawName && rawName !== entityId && !this._looksSystemLabel(rawName)) {
      return rawName;
    }
    const objectId = String(entityId).split(".").slice(1).join(".");
    const flowMatch = objectId.match(/^herald_flow_(.+)$/);
    if (flowMatch) {
      return `\u041F\u043E\u0442\u043E\u043A \xB7 ${this._friendlyFlowName(flowMatch[1])}`;
    }
    const channelFamilyMatch = objectId.match(/^herald_channel_family_(.+)$/);
    if (channelFamilyMatch) {
      return `\u0421\u0435\u043C\u0435\u0439\u0441\u0442\u0432\u043E \u043A\u0430\u043D\u0430\u043B\u043E\u0432 \xB7 ${this._friendlyChannelFamilyLabel(channelFamilyMatch[1])}`;
    }
    const match = objectId.match(/^herald_user_(.+)_(language|character|silent)$/);
    if (match) {
      const user = this._friendlyUserSlug(match[1]);
      const suffixLabels = {
        language: "\u042F\u0437\u044B\u043A",
        character: "\u041F\u0435\u0440\u0441\u043E\u043D\u0430\u0436",
        silent: "\u0417\u0432\u0443\u043A"
      };
      return `${user} \xB7 ${suffixLabels[match[2]]}`;
    }
    return this._humanizeCode(objectId || entityId);
  }
  _statusEntity() {
    return this.hass?.states?.[this._config?.status_entity ?? DEFAULT_STATUS_ENTITY];
  }
  _containsCyrillic(value) {
    return /[А-Яа-яЁё]/.test(String(value ?? ""));
  }
  _looksSystemLabel(value) {
    const raw = String(value ?? "").trim().toLowerCase();
    if (!raw) {
      return true;
    }
    return raw.startsWith("select.herald_") || raw.startsWith("switch.herald_") || raw.startsWith("sensor.") || raw.startsWith("binary_sensor.") || raw.startsWith("herald ") || raw.includes("_");
  }
  _friendlyUserSlug(slug) {
    const normalized = String(slug ?? "").trim().toLowerCase();
    const exact = {
      abrikos: "\u0410\u0431\u0440\u0438\u043A\u043E\u0441",
      aleksandr_meshcheriakov: "\u0410\u043B\u0435\u043A\u0441\u0430\u043D\u0434\u0440",
      victoria_meshchryakovf: "\u0412\u0438\u043A\u0442\u043E\u0440\u0438\u044F"
    };
    if (exact[normalized]) {
      return exact[normalized];
    }
    const topologyUsers = this._statusEntity()?.attributes?.topology?.users ?? [];
    const matchedUser = topologyUsers.find((item) => String(item?.slug ?? "").trim().toLowerCase() === normalized);
    const matchedName = String(matchedUser?.name ?? "").trim();
    if (matchedName && this._containsCyrillic(matchedName)) {
      return matchedName;
    }
    return this._humanizeCode(normalized);
  }
  _friendlyLanguageName(value) {
    const labels = {
      ru: "\u0420\u0443\u0441\u0441\u043A\u0438\u0439",
      en: "\u0410\u043D\u0433\u043B\u0438\u0439\u0441\u043A\u0438\u0439",
      es: "\u0418\u0441\u043F\u0430\u043D\u0441\u043A\u0438\u0439",
      fr: "\u0424\u0440\u0430\u043D\u0446\u0443\u0437\u0441\u043A\u0438\u0439",
      de: "\u041D\u0435\u043C\u0435\u0446\u043A\u0438\u0439",
      ca: "\u041A\u0430\u0442\u0430\u043B\u0430\u043D\u0441\u043A\u0438\u0439"
    };
    return labels[String(value ?? "").trim().toLowerCase()] ?? String(value ?? "");
  }
  _friendlyCharacterName(value) {
    const labels = {
      domovoy: "\u0414\u043E\u043C\u043E\u0432\u043E\u0439",
      hestia: "Hestia",
      plugins: "\u041F\u043B\u0430\u0433\u0438\u043D\u044B",
      jarvis: "Jarvis"
    };
    return labels[String(value ?? "").trim().toLowerCase()] ?? this._humanizeCode(value);
  }
  _friendlyNotificationTitle(item) {
    const selectedTitle = String(item?.selected_title_ru ?? "").trim();
    if (selectedTitle && this._containsCyrillic(selectedTitle)) {
      return selectedTitle;
    }
    const rawTitle = String(item?.title ?? "").trim();
    if (rawTitle && this._containsCyrillic(rawTitle) && !this._looksSystemLabel(rawTitle)) {
      return rawTitle;
    }
    const codeTitle = this._friendlyEventLabel(item?.notification_key ?? "");
    if (codeTitle && codeTitle !== "\u041D\u0435\u0442 \u0441\u043E\u0431\u044B\u0442\u0438\u044F") {
      return codeTitle;
    }
    return rawTitle || String(item?.notification_key ?? "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0435");
  }
  _friendlyDeliveryItemTitle(item, fallbackTitle = "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0435") {
    const rawTitle = String(item?.title ?? "").trim();
    if (rawTitle && this._containsCyrillic(rawTitle) && !this._looksSystemLabel(rawTitle)) {
      return rawTitle;
    }
    const eventLabel = this._friendlyEventLabel(item?.event ?? rawTitle);
    if (eventLabel && eventLabel !== "\u041D\u0435\u0442 \u0441\u043E\u0431\u044B\u0442\u0438\u044F") {
      return eventLabel;
    }
    return rawTitle || fallbackTitle;
  }
  _friendlyRoomLabel(value) {
    const raw = String(value ?? "").trim();
    if (!raw || raw === "n/a") {
      return "\u0431\u0435\u0437 \u043A\u043E\u043C\u043D\u0430\u0442\u044B";
    }
    return this._humanizeCode(raw);
  }
  _friendlyRouteLabel(item) {
    const entityId = String(item?.selected_entity ?? "").trim();
    if (!entityId || entityId === "n/a") {
      return "\u041C\u0430\u0440\u0448\u0440\u0443\u0442 \u0443\u0442\u043E\u0447\u043D\u044F\u0435\u0442\u0441\u044F \u043F\u0440\u0438 \u043F\u0440\u043E\u0432\u0435\u0440\u043A\u0435";
    }
    const entity = this.hass?.states?.[entityId];
    const friendlyName = String(entity?.attributes?.friendly_name ?? "").trim();
    if (friendlyName && !this._looksSystemLabel(friendlyName)) {
      return friendlyName;
    }
    const objectId = entityId.split(".").slice(1).join(".");
    const familyGuess = String(item?.family ?? "").trim();
    const familyLabel = familyGuess ? this._friendlyFamilyLabel(familyGuess) : "";
    if (objectId.endsWith("_alert_selected") || objectId.endsWith("_selected")) {
      return familyLabel ? `\u041C\u0430\u0440\u0448\u0440\u0443\u0442 \xB7 ${familyLabel}` : `\u041C\u0430\u0440\u0448\u0440\u0443\u0442 \xB7 ${this._humanizeCode(objectId.replace(/_alert_selected$/, "").replace(/_selected$/, ""))}`;
    }
    if (objectId.endsWith("_attention_required")) {
      return familyLabel ? `\u0412\u043D\u0438\u043C\u0430\u043D\u0438\u0435 \xB7 ${familyLabel}` : `\u0412\u043D\u0438\u043C\u0430\u043D\u0438\u0435 \xB7 ${this._humanizeCode(objectId.replace(/_attention_required$/, ""))}`;
    }
    return this._humanizeCode(objectId || entityId);
  }
  _friendlyEventLabel(code) {
    if (!code || code === "n/a" || code === "idle" || code === "none") {
      return "\u041D\u0435\u0442 \u0441\u043E\u0431\u044B\u0442\u0438\u044F";
    }
    const normalized = String(code ?? "").trim().toLowerCase();
    const exact = {
      washer_started_expensive_tariff: "\u0421\u0442\u0438\u0440\u0430\u043B\u043A\u0430 \u0437\u0430\u043F\u0443\u0449\u0435\u043D\u0430 \u043D\u0430 \u0434\u043E\u0440\u043E\u0433\u043E\u043C \u0442\u0430\u0440\u0438\u0444\u0435",
      washer_finished: "\u0421\u0442\u0438\u0440\u043A\u0430 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043D\u0430",
      wifi_guest_detected: "\u041E\u0431\u043D\u0430\u0440\u0443\u0436\u0435\u043D \u0433\u043E\u0441\u0442\u0435\u0432\u043E\u0439 Wi-Fi",
      adult_content_enabled: "\u0420\u0435\u0436\u0438\u043C 18+ \u0432\u043A\u043B\u044E\u0447\u0435\u043D",
      adult_content_disabled: "\u0420\u0435\u0436\u0438\u043C 18+ \u0432\u044B\u043A\u043B\u044E\u0447\u0435\u043D",
      morning_briefing: "\u0423\u0442\u0440\u0435\u043D\u043D\u0438\u0439 \u0431\u0440\u0438\u0444\u0438\u043D\u0433",
      evening_briefing: "\u0412\u0435\u0447\u0435\u0440\u043D\u0438\u0439 \u0431\u0440\u0438\u0444\u0438\u043D\u0433",
      daily_report: "\u0415\u0436\u0435\u0434\u043D\u0435\u0432\u043D\u044B\u0439 \u043E\u0442\u0447\u0435\u0442",
      weekly_report: "\u041D\u0435\u0434\u0435\u043B\u044C\u043D\u044B\u0439 \u043E\u0442\u0447\u0435\u0442",
      geomagnetic_storm: "\u0413\u0435\u043E\u043C\u0430\u0433\u043D\u0438\u0442\u043D\u0430\u044F \u0431\u0443\u0440\u044F",
      critical_co2: "\u041A\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043A\u0438\u0439 CO2",
      ollama_unavailable: "Ollama \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u0435\u043D",
      power_overload: "\u041F\u0435\u0440\u0435\u0433\u0440\u0443\u0437\u043A\u0430 \u043C\u043E\u0449\u043D\u043E\u0441\u0442\u0438",
      grid_quality_problem: "\u041F\u0440\u043E\u0431\u043B\u0435\u043C\u0430 \u043A\u0430\u0447\u0435\u0441\u0442\u0432\u0430 \u0441\u0435\u0442\u0438",
      grid_quality_recovered: "\u041A\u0430\u0447\u0435\u0441\u0442\u0432\u043E \u0441\u0435\u0442\u0438 \u0432\u043E\u0441\u0441\u0442\u0430\u043D\u043E\u0432\u043B\u0435\u043D\u043E",
      jump_expensive: "\u0421\u043A\u0430\u0447\u043E\u043A \u043D\u0430\u0433\u0440\u0443\u0437\u043A\u0438 \u043D\u0430 \u0434\u043E\u0440\u043E\u0433\u043E\u043C \u0442\u0430\u0440\u0438\u0444\u0435",
      punta_started: "\u041D\u0430\u0447\u0430\u043B\u0441\u044F \u043F\u0438\u043A\u043E\u0432\u044B\u0439 \u0442\u0430\u0440\u0438\u0444",
      valle_started: "\u041D\u0430\u0447\u0430\u043B\u0441\u044F \u043D\u043E\u0447\u043D\u043E\u0439 \u0442\u0430\u0440\u0438\u0444",
      report_ready: "\u041E\u0442\u0447\u0435\u0442 \u0433\u043E\u0442\u043E\u0432",
      report_skipped: "\u041E\u0442\u0447\u0435\u0442 \u043F\u0440\u043E\u043F\u0443\u0449\u0435\u043D",
      timer_status: "\u0421\u0442\u0430\u0442\u0443\u0441 \u0442\u0430\u0439\u043C\u0435\u0440\u0430",
      timer_finished: "\u0422\u0430\u0439\u043C\u0435\u0440 \u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043D",
      timer_cancelled: "\u0422\u0430\u0439\u043C\u0435\u0440 \u043E\u0442\u043C\u0435\u043D\u0435\u043D"
    };
    if (exact[normalized]) {
      return exact[normalized];
    }
    const tokenLabels = {
      ai: "\u0418\u0418",
      co2: "CO2",
      pm10: "PM10",
      pm25: "PM2.5",
      ev: "EV",
      tts: "TTS",
      wifi: "Wi-Fi",
      herald: "Herald",
      washer: "\u0441\u0442\u0438\u0440\u0430\u043B\u043A\u0430",
      guest: "\u0433\u043E\u0441\u0442\u044C",
      guests: "\u0433\u043E\u0441\u0442\u0438",
      adult: "18+",
      content: "\u043A\u043E\u043D\u0442\u0435\u043D\u0442",
      mode: "\u0440\u0435\u0436\u0438\u043C",
      started: "\u0437\u0430\u043F\u0443\u0449\u0435\u043D\u043E",
      finished: "\u0437\u0430\u0432\u0435\u0440\u0448\u0435\u043D\u043E",
      enabled: "\u0432\u043A\u043B\u044E\u0447\u0435\u043D\u043E",
      disabled: "\u043E\u0442\u043A\u043B\u044E\u0447\u0435\u043D\u043E",
      detected: "\u043E\u0431\u043D\u0430\u0440\u0443\u0436\u0435\u043D\u043E",
      recommendation: "\u0440\u0435\u043A\u043E\u043C\u0435\u043D\u0434\u0430\u0446\u0438\u044F",
      critical: "\u043A\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043A\u0438\u0439",
      warning: "\u043F\u0440\u0435\u0434\u0443\u043F\u0440\u0435\u0436\u0434\u0435\u043D\u0438\u0435",
      alert: "\u0441\u0438\u0433\u043D\u0430\u043B",
      reminder: "\u043D\u0430\u043F\u043E\u043C\u0438\u043D\u0430\u043D\u0438\u0435",
      report: "\u043E\u0442\u0447\u0435\u0442",
      power: "\u043C\u043E\u0449\u043D\u043E\u0441\u0442\u044C",
      overload: "\u043F\u0435\u0440\u0435\u0433\u0440\u0443\u0437\u043A\u0430",
      grid: "\u0441\u0435\u0442\u044C",
      quality: "\u043A\u0430\u0447\u0435\u0441\u0442\u0432\u043E",
      problem: "\u043F\u0440\u043E\u0431\u043B\u0435\u043C\u0430",
      recovered: "\u0432\u043E\u0441\u0441\u0442\u0430\u043D\u043E\u0432\u043B\u0435\u043D\u043E",
      expensive: "\u0434\u043E\u0440\u043E\u0433\u043E\u0439",
      tariff: "\u0442\u0430\u0440\u0438\u0444",
      morning: "\u0443\u0442\u0440\u0435\u043D\u043D\u0438\u0439",
      evening: "\u0432\u0435\u0447\u0435\u0440\u043D\u0438\u0439",
      timer: "\u0442\u0430\u0439\u043C\u0435\u0440",
      status: "\u0441\u0442\u0430\u0442\u0443\u0441",
      cancelled: "\u043E\u0442\u043C\u0435\u043D\u0435\u043D\u043E",
      beach: "\u043F\u043B\u044F\u0436",
      walk: "\u043F\u0440\u043E\u0433\u0443\u043B\u043A\u0430",
      window: "\u043E\u043A\u043D\u0430",
      unavailable: "\u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u043D\u043E",
      security: "\u0431\u0435\u0437\u043E\u043F\u0430\u0441\u043D\u043E\u0441\u0442\u044C",
      camera: "\u043A\u0430\u043C\u0435\u0440\u044B",
      suspicious: "\u043F\u043E\u0434\u043E\u0437\u0440\u0438\u0442\u0435\u043B\u044C\u043D\u043E",
      silence: "\u0442\u0438\u0448\u0438\u043D\u0430",
      anomaly: "\u0430\u043D\u043E\u043C\u0430\u043B\u0438\u044F",
      manual: "\u0440\u0443\u0447\u043D\u043E\u0439",
      lights: "\u0441\u0432\u0435\u0442",
      home: "\u0434\u043E\u043C",
      selected: "\u0432\u044B\u0431\u0440\u0430\u043D\u043E"
    };
    const human = normalized.split("_").map((part) => tokenLabels[part] ?? part).join(" ").replace(/\s+/g, " ").trim();
    if (!human) {
      return "\u041D\u0435\u0442 \u0441\u043E\u0431\u044B\u0442\u0438\u044F";
    }
    return human.charAt(0).toUpperCase() + human.slice(1);
  }
  _friendlySourceCount(count) {
    const number = Number(count ?? 0) || 0;
    if (number === 1) {
      return "1 \u0438\u0441\u0442\u043E\u0447\u043D\u0438\u043A";
    }
    if (number >= 2 && number <= 4) {
      return `${number} \u0438\u0441\u0442\u043E\u0447\u043D\u0438\u043A\u0430`;
    }
    return `${number} \u0438\u0441\u0442\u043E\u0447\u043D\u0438\u043A\u043E\u0432`;
  }
  _friendlyBinaryState(value) {
    if (value === "on") return "\u0432\u043A\u043B";
    if (value === "off") return "\u0432\u044B\u043A\u043B";
    if (["unknown", "unavailable"].includes(value)) return "\u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u043D\u043E";
    if (value === "n/a" || value == null || value === "") return "\u043D\u0435\u0442 \u0434\u0430\u043D\u043D\u044B\u0445";
    return this._humanizeCode(value);
  }
  _friendlyResolvedFrom(value) {
    const labels = {
      herald_fallback_switch: "Fallback-\u043F\u0435\u0440\u0435\u043A\u043B\u044E\u0447\u0430\u0442\u0435\u043B\u044C",
      room_presence_sensor: "\u0421\u0435\u043D\u0441\u043E\u0440 \u043A\u043E\u043C\u043D\u0430\u0442\u044B",
      room_presence_binary_sensor: "\u0411\u0438\u043D\u0430\u0440\u043D\u044B\u0439 \u0441\u0435\u043D\u0441\u043E\u0440 \u043A\u043E\u043C\u043D\u0430\u0442\u044B",
      real_room_sensor: "\u0420\u0435\u0430\u043B\u044C\u043D\u044B\u0439 \u0441\u0435\u043D\u0441\u043E\u0440 \u043A\u043E\u043C\u043D\u0430\u0442\u044B"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _humanizeCode(value) {
    return String(value ?? "").replace(/^select\./, "").replace(/^switch\./, "").replace(/^sensor\./, "").replace(/^binary_sensor\./, "").replaceAll("_", " ").trim();
  }
  _formatChannels(channels) {
    return (channels ?? []).map((channel) => this._friendlyChannelName(channel)).join(", ");
  }
  _setPolicySearch(value) {
    this._policyPreviews = {};
    this._policySearch = value;
    this._policyPage = 1;
    this._policyExpanded = "";
  }
  _setPolicyFamily(value) {
    this._policyPreviews = {};
    this._policyFamily = value;
    this._policyPage = 1;
    this._policyExpanded = "";
  }
  _setPolicyScope(value) {
    this._policyPreviews = {};
    this._policyScope = value;
    this._policyPage = 1;
    this._policyExpanded = "";
  }
  _filterPolicies(items) {
    const query = String(this._policySearch ?? "").trim().toLowerCase();
    const family = this._policyFamily ?? "all";
    const scope = this._policyScope ?? "all";
    return [...items].filter((item) => {
      const effective = item.effective ?? {};
      const policy = item.policy ?? {};
      const haystack = [
        item.notification_key,
        item.title,
        this._friendlyNotificationTitle(item),
        item.family,
        this._friendlyFamilyLabel(item.family),
        item.selected_entity,
        this._friendlyRouteLabel(item),
        item.selected_title_ru,
        item.family_last_event_code,
        this._friendlyEventLabel(item.family_last_event_code),
        item.selected_state_ru,
        item.selected_state,
        item.last_seen_at,
        ...item.source_files ?? [],
        ...item.effective?.channels ?? [],
        item.effective?.delivery_mode,
        item.policy?.notes
      ].join(" ").toLowerCase();
      if (query && !haystack.includes(query)) {
        return false;
      }
      if (family !== "all" && item.family !== family) {
        return false;
      }
      if (scope === "active" && !item.active) {
        return false;
      }
      if (scope === "attention" && !item.active_attention) {
        return false;
      }
      if (scope === "disabled" && effective.enabled !== false) {
        return false;
      }
      if (scope === "customized") {
        const customized = this._policyCustomized(item);
        if (!customized) {
          return false;
        }
      }
      return true;
    }).sort((left, right) => {
      const score = (item) => (item.active_attention ? 4 : 0) + (item.active ? 2 : 0) + (item.effective?.enabled === false ? 0 : 1);
      return score(right) - score(left) || String(left.title ?? left.notification_key).localeCompare(String(right.title ?? right.notification_key));
    });
  }
  _paginatePolicies(items) {
    const total = items.length;
    const totalPages = total ? Math.ceil(total / POLICY_PAGE_SIZE) : 0;
    const page = totalPages ? Math.min(Math.max(this._policyPage, 1), totalPages) : 1;
    const start = (page - 1) * POLICY_PAGE_SIZE;
    return {
      items: items.slice(start, start + POLICY_PAGE_SIZE),
      page,
      totalPages
    };
  }
  _humanizeFamily(value) {
    return String(value ?? "general").replaceAll("_", " ");
  }
  _togglePolicyExpanded(notificationKey) {
    this._policyPreviews = {};
    this._policyExpanded = this._policyExpanded === notificationKey ? "" : notificationKey;
    if (this._policyExpanded) {
      void this.updateComplete.then(() => {
        const heading = this.renderRoot?.querySelector(".policy-editor-heading h4");
        heading?.focus({ preventScroll: true });
        heading?.scrollIntoView({ block: "start", behavior: "auto" });
      });
    }
  }
  _setPolicyPage(page) {
    this._policyPreviews = {};
    this._policyPage = Math.max(1, page);
  }
  async _refreshPolicies() {
    if (!this.hass) {
      return;
    }
    await this.hass.callService("herald", "refresh_notification_registry", {
      force: true
    });
  }
  _normalizedPolicy(policy = {}) {
    const rawCooldown = policy.cooldown_override;
    return {
      enabled: policy.enabled !== false,
      delivery_mode: policy.delivery_mode ?? "inherit",
      channels: Array.isArray(policy.channels) ? [...policy.channels] : String(policy.channels ?? "").split(",").map((part) => part.trim()).filter(Boolean),
      users: Array.isArray(policy.users) ? [...policy.users] : null,
      target_room: policy.target_room || null,
      presence: policy.presence ?? "any",
      quiet_hours: policy.quiet_hours ?? "inherit",
      level_override: policy.level_override ?? "",
      cooldown_override: rawCooldown == null || rawCooldown === "" ? "" : Number(rawCooldown),
      notes: policy.notes ?? ""
    };
  }
  _policyItem(item) {
    const saved = this._policySaved[item.notification_key];
    return saved && saved.sourceVersion === JSON.stringify(item.policy ?? {}) ? { ...item, policy: saved.response.policy, effective: saved.response.effective ?? item.effective } : item;
  }
  _policyPayload(item) {
    const saved = this._policyItem(item);
    return this._normalizedPolicy({ ...saved.policy, ...this._policyDrafts[item.notification_key] });
  }
  _policyDirty(item) {
    return JSON.stringify(this._policyPayload(item)) !== JSON.stringify(this._normalizedPolicy(this._policyItem(item).policy));
  }
  _policyRouteSummary(policy, flow) {
    if (policy.enabled === false || policy.delivery_mode === "disabled") return "\u0414\u043E\u0441\u0442\u0430\u0432\u043A\u0430 \u043E\u0442\u043A\u043B\u044E\u0447\u0435\u043D\u0430";
    const mode = policy.delivery_mode ?? "inherit";
    if (mode === "inherit") return flow ? `\u041F\u043E \u043E\u0431\u0449\u0435\u043C\u0443 \u043F\u0440\u0430\u0432\u0438\u043B\u0443 \u043F\u043E\u0442\u043E\u043A\u0430 \xAB${this._friendlyFlowName(flow)}\xBB` : "\u041F\u043E \u043E\u0431\u0449\u0435\u043C\u0443 \u043F\u0440\u0430\u0432\u0438\u043B\u0443 \u043F\u043E\u0442\u043E\u043A\u0430 \u0438 \u0434\u043E\u043C\u0430";
    if (mode === "custom") return policy.channels?.length ? `\u0422\u043E\u043B\u044C\u043A\u043E \u0432\u044B\u0431\u0440\u0430\u043D\u043D\u044B\u0435 \u043A\u0430\u043D\u0430\u043B\u044B: ${this._formatChannels(policy.channels)}` : "\u041A\u0430\u043D\u0430\u043B\u044B \u043D\u0435 \u0432\u044B\u0431\u0440\u0430\u043D\u044B \u2014 \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0438 \u043D\u0435 \u0431\u0443\u0434\u0435\u0442";
    return `${this._friendlyDeliveryMode(mode)}; \u0438\u0442\u043E\u0433 \u043E\u043F\u0440\u0435\u0434\u0435\u043B\u044F\u0435\u0442\u0441\u044F \u043F\u0440\u043E\u0432\u0435\u0440\u043A\u043E\u0439`;
  }
  _clearPolicyPreview(key) {
    const next = { ...this._policyPreviews };
    delete next[key];
    this._policyPreviews = next;
  }
  _discardPolicyDraft(key) {
    const drafts = { ...this._policyDrafts };
    delete drafts[key];
    this._policyDrafts = drafts;
    this._policyRevisions[key] = (this._policyRevisions[key] ?? 0) + 1;
    this._clearPolicyPreview(key);
    this._policyFeedback = { ...this._policyFeedback, [key]: { type: "success", message: "\u0418\u0437\u043C\u0435\u043D\u0435\u043D\u0438\u044F \u043E\u0442\u043C\u0435\u043D\u0435\u043D\u044B. \u041F\u043E\u043A\u0430\u0437\u0430\u043D\u043E \u0441\u043E\u0445\u0440\u0430\u043D\u0451\u043D\u043D\u043E\u0435 \u043F\u0440\u0430\u0432\u0438\u043B\u043E." } };
  }
  _setPolicyScenario(key, scenario) {
    this._policyScenarios = { ...this._policyScenarios, [key]: scenario };
    this._clearPolicyPreview(key);
  }
  async _policyService(service, data) {
    if (!this.hass?.callWS) throw new Error("\u0421\u043E\u0435\u0434\u0438\u043D\u0435\u043D\u0438\u0435 \u0441 Home Assistant \u043D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u043D\u043E. \u041E\u0431\u043D\u043E\u0432\u0438\u0442\u0435 \u0441\u0442\u0440\u0430\u043D\u0438\u0446\u0443.");
    const serviceData = { ...data };
    if (this._config?.entry_id) serviceData.entry_id = this._config.entry_id;
    const result = await this.hass.callWS({ type: "call_service", domain: "herald", service, service_data: serviceData, return_response: true });
    if (!result?.response || typeof result.response !== "object") throw new Error("Home Assistant \u043D\u0435 \u0432\u0435\u0440\u043D\u0443\u043B \u0440\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442. \u041E\u0431\u043D\u043E\u0432\u0438\u0442\u0435 \u0440\u0435\u0435\u0441\u0442\u0440 \u0438 \u043F\u0440\u043E\u0432\u0435\u0440\u044C\u0442\u0435 \u0441\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u0435 \u043F\u0440\u0430\u0432\u0438\u043B\u0430.");
    return result.response;
  }
  _policyError(error) {
    return error?.message ? String(error.message) : "\u041D\u0435 \u0443\u0434\u0430\u043B\u043E\u0441\u044C \u0432\u044B\u043F\u043E\u043B\u043D\u0438\u0442\u044C \u0434\u0435\u0439\u0441\u0442\u0432\u0438\u0435. \u041F\u0440\u043E\u0432\u0435\u0440\u044C\u0442\u0435 \u043F\u043E\u0434\u043A\u043B\u044E\u0447\u0435\u043D\u0438\u0435 \u0438 \u0436\u0443\u0440\u043D\u0430\u043B Home Assistant.";
  }
  _validatePolicy(policy) {
    if (policy.cooldown_override !== "" && (!Number.isInteger(policy.cooldown_override) || policy.cooldown_override < 0 || policy.cooldown_override > 86400)) {
      throw new Error("\u0418\u043D\u0442\u0435\u0440\u0432\u0430\u043B \u0434\u043E\u043B\u0436\u0435\u043D \u0431\u044B\u0442\u044C \u0446\u0435\u043B\u044B\u043C \u0447\u0438\u0441\u043B\u043E\u043C \u043E\u0442 0 \u0434\u043E 86400 \u0441\u0435\u043A\u0443\u043D\u0434 \u0438\u043B\u0438 \u043F\u0443\u0441\u0442\u044B\u043C.");
    }
  }
  async _previewPolicy(item) {
    const key = String(item.notification_key ?? "");
    const token = ++this._previewSequence;
    const scenario = this._policyScenarios[key] ?? "current";
    const policy = this._policyPayload(item);
    this._policyPreviews = { ...this._policyPreviews, [key]: { loading: true, token } };
    try {
      this._validatePolicy(policy);
      const result = await this._policyService("preview_notification_policy", { notification_key: key, policy, scenario });
      if (this._policyPreviews[key]?.token !== token) return;
      if (!result.explanation?.summary) throw new Error("\u0421\u0435\u0440\u0432\u0435\u0440 \u043D\u0435 \u0432\u0435\u0440\u043D\u0443\u043B \u043E\u0431\u044A\u044F\u0441\u043D\u0435\u043D\u0438\u0435 \u043C\u0430\u0440\u0448\u0440\u0443\u0442\u0430.");
      this._policyPreviews = { ...this._policyPreviews, [key]: { loading: false, token, result } };
    } catch (error) {
      if (this._policyPreviews[key]?.token !== token) return;
      this._policyPreviews = { ...this._policyPreviews, [key]: { loading: false, token, error: this._policyError(error) } };
    }
  }
  async _mutatePolicy(item, service, payload, message, { clearDraft = false } = {}) {
    if (this._busyPolicy) return;
    const key = String(item.notification_key ?? "");
    const revision = this._policyRevisions[key] ?? 0;
    this._busyPolicy = key;
    this._clearPolicyPreview(key);
    this._policyFeedback = { ...this._policyFeedback, [key]: void 0 };
    try {
      const response = await this._policyService(service, { notification_key: key, ...payload });
      if (!response.policy || response.notification_key !== key) throw new Error("\u041E\u0442\u0432\u0435\u0442 \u0441\u0435\u0440\u0432\u0435\u0440\u0430 \u043D\u0435 \u0441\u043E\u0434\u0435\u0440\u0436\u0438\u0442 \u0441\u043E\u0445\u0440\u0430\u043D\u0451\u043D\u043D\u043E\u0435 \u043F\u0440\u0430\u0432\u0438\u043B\u043E. \u041E\u0431\u043D\u043E\u0432\u0438\u0442\u0435 \u0440\u0435\u0435\u0441\u0442\u0440.");
      const source = this._statusEntity()?.attributes?.notification_registry?.items?.find((entry) => entry.notification_key === key) ?? item;
      this._policySaved = {
        ...this._policySaved,
        [key]: JSON.stringify(source.policy ?? {}) === JSON.stringify(response.policy) ? void 0 : { sourceVersion: JSON.stringify(source.policy ?? {}), response }
      };
      if (clearDraft && (this._policyRevisions[key] ?? 0) === revision) {
        const drafts = { ...this._policyDrafts };
        delete drafts[key];
        this._policyDrafts = drafts;
      }
      const suffix = (this._policyRevisions[key] ?? 0) !== revision ? " \u0411\u043E\u043B\u0435\u0435 \u043D\u043E\u0432\u044B\u0435 \u0438\u0437\u043C\u0435\u043D\u0435\u043D\u0438\u044F \u043E\u0441\u0442\u0430\u044E\u0442\u0441\u044F \u0432 \u0447\u0435\u0440\u043D\u043E\u0432\u0438\u043A\u0435." : "";
      this._policyFeedback = { ...this._policyFeedback, [key]: { type: "success", message: message + suffix } };
    } catch (error) {
      this._policyFeedback = { ...this._policyFeedback, [key]: { type: "error", message: this._policyError(error) } };
    } finally {
      this._busyPolicy = "";
    }
  }
  async _togglePolicyEnabled(item) {
    item = this._policyItem(item);
    const enable = !(item.effective?.enabled ?? true);
    const payload = { enabled: enable };
    if (enable && item.policy?.delivery_mode === "disabled") payload.delivery_mode = "inherit";
    await this._mutatePolicy(item, "set_notification_policy", payload, enable ? "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0435 \u0432\u043A\u043B\u044E\u0447\u0435\u043D\u043E." : "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u0435 \u043E\u0442\u043A\u043B\u044E\u0447\u0435\u043D\u043E.");
  }
  async _savePolicy(item) {
    const policy = this._policyPayload(item);
    try {
      this._validatePolicy(policy);
    } catch (error) {
      this._policyFeedback = { ...this._policyFeedback, [item.notification_key]: { type: "error", message: this._policyError(error) } };
      return;
    }
    await this._mutatePolicy(item, "set_notification_policy", policy, "\u041F\u0440\u0430\u0432\u0438\u043B\u043E \u0441\u043E\u0445\u0440\u0430\u043D\u0435\u043D\u043E.", { clearDraft: true });
  }
  async _resetPolicy(item) {
    await this._mutatePolicy(item, "reset_notification_policy", {}, "\u0412\u043E\u0441\u0441\u0442\u0430\u043D\u043E\u0432\u043B\u0435\u043D\u043E \u043E\u0431\u0449\u0435\u0435 \u043F\u0440\u0430\u0432\u0438\u043B\u043E.", { clearDraft: true });
  }
};
__publicField(HeraldCard, "properties", {
  hass: { attribute: false },
  _config: { state: true },
  _busyFlow: { state: true },
  _busyPolicy: { state: true },
  _policyDrafts: { state: true },
  _policySearch: { state: true },
  _policyFamily: { state: true },
  _policyScope: { state: true },
  _policyPage: { state: true },
  _policyExpanded: { state: true },
  _policySaved: { state: true },
  _policyFeedback: { state: true },
  _policyPreviews: { state: true },
  _policyScenarios: { state: true },
  _controlActions: { state: true },
  _configurationResponse: { state: true },
  _configurationBusy: { state: true },
  _configurationFeedback: { state: true }
});
HeraldCard.styles = i`
    :host {
      display: block;
    }

    ha-card {
      color: var(--primary-text-color);
      background: var(--ha-card-background, var(--card-background-color));
    }

    .shell {
      padding: 16px;
      display: grid;
      gap: 16px;
    }

    .hero {
      display: grid;
      gap: 14px;
    }

    .hero-panel .panel-shell {
      gap: 16px;
    }

    .eyebrow {
      margin: 0;
      text-transform: uppercase;
      letter-spacing: 0.12em;
      font-size: 0.72rem;
      color: var(--secondary-text-color);
    }

    h2,
    h3,
    p {
      margin: 0;
    }

    h2 {
      font-size: 1.4rem;
      line-height: 1.2;
      margin-top: 2px;
    }

    .subhead {
      color: var(--secondary-text-color);
      margin-top: 8px;
    }

    .stats,
    .flow-grid,
    .language-grid,
    .room-grid,
    .character-grid,
    .mute-grid {
      display: grid;
      gap: 12px;
    }

    .stats {
      grid-template-columns: repeat(auto-fit, minmax(120px, 1fr));
    }

    .stats.compact {
      grid-template-columns: repeat(auto-fit, minmax(90px, 1fr));
    }

    .stat,
    .panel,
    .language-card,
    .policy-card,
    .room-card,
    .notification,
    .flow {
      border-radius: 14px;
      border: 1px solid var(--divider-color);
      background: var(--secondary-background-color);
    }

    .stat {
      padding: 14px;
      display: grid;
      gap: 6px;
    }

    .stat span,
    .panel-header span,
    footer,
    .flow-state {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .panel {
      overflow: hidden;
      background: var(--ha-card-background, var(--card-background-color));
    }

    .panel-shell {
      padding: 14px;
      display: grid;
      gap: 12px;
    }

    .panel-header {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: baseline;
      flex-wrap: wrap;
    }

    .flow-grid {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .flow {
      appearance: none;
      text-align: left;
      padding: 12px;
      cursor: pointer;
      display: grid;
      gap: 6px;
      transition: border-color 160ms ease, background 160ms ease;
      color: inherit;
    }

    .flow:hover {
      border-color: var(--primary-color);
    }

    .flow-name {
      font-weight: 700;
    }

    .flow.enabled {
      background: var(--ha-card-background, var(--card-background-color));
    }

    .flow.disabled {
      background: color-mix(in srgb, var(--state-unavailable-color, #9e9e9e) 12%, var(--secondary-background-color));
    }

    .language-grid {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .character-grid,
    .mute-grid {
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }

    .policy-grid-advanced {
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .language-card {
      padding: 14px;
      display: grid;
      gap: 10px;
    }

    .room-grid {
      grid-template-columns: repeat(auto-fit, minmax(220px, 1fr));
    }

    .room-card {
      padding: 14px;
      display: grid;
      gap: 10px;
    }

    .room-head,
    .room-meta {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
    }

    .room-meta {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .room-toggle {
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      padding: 10px 12px;
      background: var(--ha-card-background, var(--card-background-color));
      color: inherit;
      font: inherit;
      cursor: pointer;
      text-align: left;
    }

    .room-toggle:hover {
      border-color: var(--primary-color);
    }

    .secondary-action {
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      padding: 10px 12px;
      background: var(--ha-card-background, var(--card-background-color));
      color: inherit;
      font: inherit;
      cursor: pointer;
    }

    .secondary-action:hover {
      border-color: var(--primary-color);
    }

    .secondary-action:disabled,
    .room-toggle:disabled {
      opacity: 0.6;
      cursor: default;
    }

    .policy-card {
      padding: 14px;
      display: grid;
      gap: 10px;
    }

    .policy-toolbar {
      display: grid;
      gap: 12px;
      grid-template-columns: repeat(auto-fit, minmax(180px, 1fr));
    }

    .policy-card.disabled {
      opacity: 0.8;
      background: color-mix(in srgb, var(--state-unavailable-color, #9e9e9e) 10%, var(--secondary-background-color));
    }

    .policy-head,
    .policy-meta,
    .policy-actions {
      display: flex;
      justify-content: space-between;
      gap: 10px;
      flex-wrap: wrap;
      align-items: center;
    }

    .policy-meta {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .policy-actions {
      justify-content: flex-end;
    }

    .policy-table-wrap {
      overflow-x: auto;
      border: 1px solid var(--divider-color);
      border-radius: 14px;
      background: var(--ha-card-background, var(--card-background-color));
    }

    .policy-table {
      width: 100%;
      border-collapse: collapse;
      min-width: 980px;
    }

    .policy-table th,
    .policy-table td {
      padding: 12px;
      border-bottom: 1px solid var(--divider-color);
      vertical-align: top;
      text-align: left;
    }

    .policy-table th {
      color: var(--secondary-text-color);
      font-size: 0.8rem;
      text-transform: uppercase;
      letter-spacing: 0.04em;
      background: color-mix(in srgb, var(--secondary-background-color) 85%, transparent);
    }

    .policy-table tbody tr:last-child td {
      border-bottom: none;
    }

    .policy-row.is-active {
      background: color-mix(in srgb, var(--success-color, #43a047) 7%, transparent);
    }

    .policy-row.is-attention {
      background: color-mix(in srgb, var(--error-color, #e53935) 8%, transparent);
    }

    .policy-row-main {
      display: grid;
      gap: 4px;
    }

    .policy-table-subline {
      color: var(--secondary-text-color);
      font-size: 0.82rem;
      line-height: 1.35;
    }

    .policy-status-stack,
    .policy-inline-actions {
      display: flex;
      gap: 8px;
      flex-wrap: wrap;
      align-items: center;
    }

    .policy-status {
      padding: 4px 10px;
      border-radius: 999px;
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
      background: color-mix(in srgb, var(--divider-color) 45%, transparent);
    }

    .policy-status.enabled {
      background: color-mix(in srgb, var(--success-color, #43a047) 14%, transparent);
      color: var(--success-color, #43a047);
    }

    .policy-status.disabled {
      background: color-mix(in srgb, var(--state-unavailable-color, #9e9e9e) 18%, transparent);
      color: var(--state-unavailable-color, #9e9e9e);
    }

    .policy-editor-row td {
      background: color-mix(in srgb, var(--secondary-background-color) 88%, transparent);
    }

    .policy-editor-container { padding: 18px; border: 1px solid var(--divider-color); border-radius: 14px; margin-bottom: 16px; min-width: 0; }
    .policy-provenance { margin: 12px 0; }
    .policy-provenance summary { cursor: pointer; }
    .policy-provenance dl { display: grid; gap: 10px; }
    .policy-provenance dt { font-weight: 600; }
    .policy-provenance dd { margin: 4px 0 0; }
    .policy-provenance small { display: block; color: var(--secondary-text-color); }
    .policy-card-editor {
      border: none;
      padding: 0;
      background: transparent;
    }

    .policy-editor-heading, .policy-preview-heading { display: flex; justify-content: space-between; align-items: flex-start; gap: 12px; flex-wrap: wrap; }
    .policy-editor-heading h4 { margin: 0 0 6px; font-size: 1.05rem; }
    .policy-hint { color: var(--secondary-text-color); font-size: 0.85rem; line-height: 1.5; margin: 6px 0; }
    .policy-rule-summary { margin: 0; font-weight: 600; }
    .policy-target-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 14px; }
    .policy-rule-section { min-width: 0; }
    .policy-rule-section h5 { font-size: 1rem; margin: 0 0 10px; }
    .policy-user-options { margin-top: 10px; }
    .policy-user-options .policy-channel { max-width: 100%; overflow-wrap: anywhere; }
    .policy-saved-targets { overflow-wrap: anywhere; }
    .policy-draft-targets { margin: 0; line-height: 1.5; overflow-wrap: anywhere; }
    .policy-enabled { display: flex; align-items: center; gap: 8px; }
    .policy-channel-fieldset { border: 1px solid var(--divider-color); border-radius: 10px; padding: 12px; min-width: 0; }
    .policy-advanced { border-top: 1px solid var(--divider-color); padding-top: 12px; }
    .policy-advanced summary { cursor: pointer; padding: 6px 0; }
    .policy-advanced .policy-grid { margin-top: 12px; }
    .policy-preview, .policy-last-decision { padding: 14px; border-radius: 12px; background: var(--secondary-background-color); }
    .policy-preview-controls { display: flex; flex-wrap: wrap; align-items: flex-end; gap: 12px; margin-top: 12px; }
    .policy-preview-controls label { display: grid; gap: 6px; flex: 1; min-width: 150px; }
    .policy-preview-controls select { padding: 9px; border-radius: 8px; background: var(--card-background-color); color: var(--primary-text-color); border: 1px solid var(--divider-color); }
    .policy-feedback { padding: 12px; border-radius: 10px; margin: 0; line-height: 1.5; }
    .policy-feedback.success { background: color-mix(in srgb, var(--success-color, #43a047) 12%, transparent); }
    .policy-feedback.error { background: color-mix(in srgb, var(--error-color, #e53935) 12%, transparent); color: var(--error-color, #e53935); }
    .policy-explanation { margin-top: 14px; padding-top: 14px; border-top: 1px solid var(--divider-color); line-height: 1.5; }
    .policy-explanation ol { padding-left: 20px; }
    .policy-explanation li { margin-bottom: 6px; }
    .policy-last-decision p { margin: 6px 0; }
    .primary-action { font-weight: 700; }
    .policy-pager {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      align-items: center;
      flex-wrap: wrap;
    }

    .policy-field {
      background: var(--ha-card-background, var(--card-background-color));
      border: 1px solid var(--divider-color);
    }
    .policy-field select { min-width: 0; max-width: 100%; width: 100%; box-sizing: border-box; }
    .configuration-overview { display: grid; gap: 12px; margin-top: 16px; }
    .configuration-heading { display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 10px; }
    .configuration-heading h4 { margin: 0; font-size: 1rem; overflow-wrap: anywhere; }
    .configuration-restrictions { margin: 0; padding: 0; list-style: none; display: grid; gap: 8px; }
    .configuration-restrictions li { padding: 12px; border-left: 3px solid var(--warning-color, #e5a100); border-radius: 8px; background: var(--secondary-background-color); }
    .configuration-restrictions p { margin: 4px 0 0; line-height: 1.5; }
    .restriction-action { margin-top: 8px; }
    .configuration-counts { display: flex; flex-wrap: wrap; gap: 8px 18px; color: var(--secondary-text-color); }
    .channel-controls-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(min(100%, 300px), 1fr)); gap: 14px; }
    .channel-control-card { padding: 16px; border: 1px solid var(--divider-color); border-radius: 14px; display: grid; align-content: start; gap: 12px; min-width: 0; overflow-wrap: anywhere; }
    .channel-control-card .channel-level { padding: 0; background: transparent; border: 0; }
    .channel-level select, .language-card select { min-width: 0; max-width: 100%; width: 100%; box-sizing: border-box; }
    .channel-checks { margin: 0; padding-left: 20px; line-height: 1.5; }
    .channel-checks li + li { margin-top: 6px; }
    .channel-checks .attention { color: var(--error-color, #b72f37); }
    button:disabled, select:disabled { cursor: not-allowed; opacity: 0.6; }

    .policy-filter {
      background: var(--ha-card-background, var(--card-background-color));
      border: 1px solid var(--divider-color);
    }

    .policy-channel-summary {
      color: var(--secondary-text-color);
      font-size: 0.85rem;
    }

    .policy-channel-grid {
      display: flex;
      flex-wrap: wrap;
      gap: 8px;
    }

    .policy-channel {
      border: 1px solid var(--divider-color);
      border-radius: 999px;
      padding: 8px 10px;
      background: var(--ha-card-background, var(--card-background-color));
      color: inherit;
      font: inherit;
      cursor: pointer;
    }

    .policy-channel.selected {
      border-color: var(--primary-color);
      background: color-mix(in srgb, var(--primary-color) 14%, transparent);
      color: var(--primary-color);
    }

    .policy-channel:disabled {
      opacity: 0.6;
      cursor: default;
    }

    select,
    input {
      border: 1px solid var(--divider-color);
      border-radius: 12px;
      padding: 10px 12px;
      background: var(--ha-card-background, var(--card-background-color));
      font: inherit;
      color: inherit;
    }

    .list {
      display: grid;
      gap: 10px;
    }

    .notification {
      padding: 14px;
      display: grid;
      gap: 10px;
    }

    .event-text {
      color: var(--secondary-text-color);
      line-height: 1.5;
      overflow-wrap: anywhere;
    }

    .event-entry + .event-entry {
      border-top: 1px solid var(--divider-color);
    }

    .older-events {
      border-top: 1px solid var(--divider-color);
    }

    .older-events > summary {
      padding: 12px 0;
      cursor: pointer;
      color: var(--primary-color);
    }

    .event-entry summary {
      display: flex;
      align-items: flex-start;
      gap: 12px;
      padding: 16px 0;
      cursor: pointer;
      list-style: none;
    }

    .event-entry summary::-webkit-details-marker {
      display: none;
    }

    .event-entry summary:focus-visible {
      outline: 2px solid var(--primary-color);
      outline-offset: 4px;
    }

    .event-entry summary ha-icon {
      flex: 0 0 24px;
      color: var(--secondary-text-color);
    }

    .event-entry summary .event-chevron {
      flex-basis: 18px;
      --mdc-icon-size: 18px;
    }

    .event-entry[open] .event-chevron {
      transform: rotate(180deg);
    }

    .event-preview {
      min-width: 0;
      flex: 1;
      display: grid;
      gap: 6px;
      line-height: 1.4;
    }

    .event-preview strong {
      font-size: 1rem;
      font-weight: 500;
      overflow-wrap: anywhere;
    }

    .event-description {
      color: var(--secondary-text-color);
      font-size: 0.875rem;
      display: -webkit-box;
      -webkit-box-orient: vertical;
      -webkit-line-clamp: 2;
      overflow: hidden;
      overflow-wrap: anywhere;
    }

    .event-entry time {
      flex: 0 0 auto;
      color: var(--secondary-text-color);
      font-size: 0.875rem;
      line-height: 1.6;
    }

    .event-content {
      display: grid;
      gap: 12px;
      padding: 0 0 16px 36px;
    }

    .event-content .event-text {
      white-space: pre-wrap;
    }

    .event-date {
      color: var(--secondary-text-color);
      font-size: 0.875rem;
    }

    .compact-panel {
      border-radius: var(--ha-card-border-radius, 12px);
      border: var(--ha-card-border-width, 1px) solid var(--ha-card-border-color, var(--divider-color));
    }

    .compact-panel .panel-shell {
      padding: 16px;
    }

    .compact-panel h3 {
      font-size: var(--ha-card-header-font-size, 24px);
      font-weight: normal;
      line-height: 1.4;
    }

    .compact-panel .policy-table {
      min-width: 0;
    }

    .compact-panel .policy-table th:nth-child(2),
    .compact-panel .policy-table td:nth-child(2),
    .compact-panel .policy-table th:nth-child(6),
    .compact-panel .policy-table td:nth-child(6),
    .compact-panel .policy-table th:nth-child(7),
    .compact-panel .policy-table td:nth-child(7) {
      display: none;
    }

    .compact-panel .list {
      gap: 0;
    }

    .compact-panel .notification {
      padding: 16px 0;
      border: 0;
      border-radius: 0;
      background: transparent;
    }

    .compact-panel .notification + .notification {
      border-top: 1px solid var(--divider-color);
    }

    .compact-panel .notification-head .pill {
      padding: 0;
      background: transparent;
      text-transform: none;
      font-weight: normal;
    }

    .notification-head,
    footer {
      display: flex;
      justify-content: space-between;
      gap: 12px;
      flex-wrap: wrap;
    }

    .pill {
      padding: 4px 10px;
      border-radius: 999px;
      background: color-mix(in srgb, var(--primary-color) 12%, transparent);
      color: var(--primary-color);
      font-size: 0.78rem;
      font-weight: 700;
      text-transform: uppercase;
    }

    .pill.active {
      background: color-mix(in srgb, var(--success-color, #43a047) 14%, transparent);
      color: var(--success-color, #43a047);
    }

    .pill.danger {
      background: color-mix(in srgb, var(--error-color, #e53935) 14%, transparent);
      color: var(--error-color, #e53935);
    }

    .pill.custom {
      background: color-mix(in srgb, var(--warning-color, #fb8c00) 14%, transparent);
      color: var(--warning-color, #fb8c00);
    }

    .empty {
      padding: 18px;
      border-radius: 14px;
      background: var(--secondary-background-color);
      color: var(--secondary-text-color);
      text-align: center;
    }

    @media (max-width: 640px) {
      .policy-target-grid { grid-template-columns: 1fr; }
      .policy-table { min-width: 0; }
      .policy-table thead { display: none; }
      .policy-table tbody, .policy-table tr { display: block; }
      .policy-table tr { padding: 8px 0; border-bottom: 1px solid var(--divider-color); }
      .policy-table td { display: none; }
      .policy-table td:nth-child(1), .policy-table td:nth-child(3), .policy-table td:nth-child(5), .policy-table td:nth-child(8) { display: block; border: 0; padding: 7px 12px; }
      .policy-inline-actions { justify-content: flex-start; }
      .shell {
        padding: 18px;
      }

      h2 {
        font-size: 1.35rem;
      }

      .policy-pager {
        align-items: stretch;
      }
    }
  `;
if (!customElements.get("herald-card")) {
  customElements.define("herald-card", HeraldCard);
}
var registerHeraldVariant = (tagName, defaultViewMode) => {
  if (customElements.get(tagName)) {
    return;
  }
  class HeraldVariantCard extends HeraldCard {
  }
  HeraldVariantCard.viewMode = defaultViewMode;
  customElements.define(tagName, HeraldVariantCard);
};
registerHeraldVariant("ha-herald-general", "general");
registerHeraldVariant("ha-herald-policies", "policies");
registerHeraldVariant("ha-herald-policy-guide", "policy-guide");
registerHeraldVariant("ha-herald-flows", "flows");
registerHeraldVariant("ha-herald-languages", "languages");
registerHeraldVariant("ha-herald-characters", "characters");
registerHeraldVariant("ha-herald-mute", "mute");
registerHeraldVariant("ha-herald-rooms", "rooms");
registerHeraldVariant("ha-herald-queue", "queue");
registerHeraldVariant("ha-herald-controls", "controls");
registerHeraldVariant("ha-herald-feed", "feed");
registerHeraldVariant("ha-herald-recent", "recent");
registerHeraldVariant("ha-herald-overview", "overview");

// frontend/dashboard-model.js
var DASHBOARD_TABS = [
  ["overview", "\u041E\u0431\u0437\u043E\u0440", "mdi:view-dashboard"],
  ["rules", "\u041F\u0440\u0430\u0432\u0438\u043B\u0430", "mdi:cog"],
  ["delivery", "\u0414\u043E\u0441\u0442\u0430\u0432\u043A\u0430", "mdi:send"],
  ["analytics", "\u0410\u043D\u0430\u043B\u0438\u0442\u0438\u043A\u0430", "mdi:chart-bar"],
  ["controls", "\u0423\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u0438\u0435", "mdi:wrench"],
  ["diagnostics", "\u0414\u0438\u0430\u0433\u043D\u043E\u0441\u0442\u0438\u043A\u0430", "mdi:pulse"]
];
function eventIdentity(item, index = 0) {
  return String(item?.notification_id || `${item?.timestamp ?? ""}|${item?.event ?? item?.title ?? ""}|${index}`);
}
function eventOutcome(item) {
  const results = Array.isArray(item?.results) ? item.results : [];
  const sent = results.filter((result) => result.status === "sent").length;
  const errors = results.filter((result) => result.status === "error").length;
  if (errors) return { label: sent ? `\u041E\u0442\u043F\u0440\u0430\u0432\u043A\u0438: ${sent} \xB7 \u041E\u0448\u0438\u0431\u043A\u0438: ${errors}` : `\u041E\u0448\u0438\u0431\u043A\u0438: ${errors}`, tone: "error" };
  if (sent) return { label: `\u041E\u0442\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u043E \u0432 ${sent} ${sent === 1 ? "\u043A\u0430\u043D\u0430\u043B" : sent < 5 ? "\u043A\u0430\u043D\u0430\u043B\u0430" : "\u043A\u0430\u043D\u0430\u043B\u043E\u0432"}`, tone: "success" };
  if (results.some((result) => result.status === "dropped")) return { label: "\u0414\u043E\u0441\u0442\u0430\u0432\u043A\u0430 \u043F\u0440\u043E\u043F\u0443\u0449\u0435\u043D\u0430", tone: "warning" };
  return { label: "\u0420\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442 \u043E\u0442\u043F\u0440\u0430\u0432\u043A\u0438 \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D", tone: "muted" };
}
function eventIcon(item) {
  const code = `${item?.event ?? ""} ${item?.flow ?? ""} ${item?.title ?? ""}`.toLowerCase();
  if (/washer|laundry|стир/.test(code)) return "mdi:washing-machine";
  if (/battery|батар|заряд/.test(code)) return "mdi:battery-alert-variant-outline";
  if (/timer|таймер/.test(code)) return "mdi:timer-sand";
  if (/report|brief|отч|бриф/.test(code)) return "mdi:text-box-outline";
  if (/security|alarm|охран/.test(code)) return "mdi:shield-home-outline";
  return "mdi:bell-outline";
}
function ruleForEvent(item, registry) {
  if (!item) return null;
  const key = item.notification_key ?? item.explanation?.notification_key;
  if (key) return registry.find((rule) => rule.notification_key === key) ?? null;
  const matches = registry.filter((rule) => rule.notification_key === item.event || rule.event === item.event);
  return matches.length === 1 ? matches[0] : null;
}
function knownCounter(value) {
  return value !== null && value !== void 0 && value !== "" && Number.isFinite(Number(value)) ? value : "\u2014";
}

// frontend/herald-dashboard.js
var HeraldDashboardSection = class extends HeraldCard {
  set settings(value) {
    const signature = JSON.stringify(value);
    if (signature === this._settingsSignature) return;
    this._settingsSignature = signature;
    this.setConfig(value);
  }
};
__publicField(HeraldDashboardSection, "styles", [HeraldCard.styles, i`
    :host { --ha-card-background: #092a36; --primary-text-color: #d9edf4; --secondary-text-color: #93b7c6; --primary-color: #43c4e9; }
    ha-card.panel, ha-card { background: transparent; border: 0; box-shadow: none; }
    .panel-shell { padding: 0; }
    .panel-header h3 { font-size: 22px; }
    input, select { color-scheme: dark; }
  `]);
var HeraldDashboard = class extends HeraldCard {
  constructor() {
    super();
    this._tab = "overview";
    this._subview = "channels";
    this._selectedEvent = "";
    this._detailOpen = false;
    this._ruleKey = "";
    this._now = /* @__PURE__ */ new Date();
    this._numberErrors = {};
    this._eventFeedback = "";
    this._eventBusy = false;
  }
  connectedCallback() {
    super.connectedCallback();
    this._clockTimer = setInterval(() => {
      this._now = /* @__PURE__ */ new Date();
    }, 6e4);
  }
  disconnectedCallback() {
    clearInterval(this._clockTimer);
    super.disconnectedCallback();
  }
  getCardSize() {
    return 12;
  }
  _data() {
    return this._statusEntity()?.attributes ?? {};
  }
  _events() {
    const items = this.hass?.states[this._config?.today_entity]?.attributes?.recent_notifications;
    return Array.isArray(items) ? items.filter((item) => item && typeof item === "object") : [];
  }
  _selected() {
    const items = this._events();
    return items.find((item, index) => eventIdentity(item, index) === this._selectedEvent) ?? items[0] ?? null;
  }
  _switchTab(tab) {
    if (!DASHBOARD_TABS.some(([key]) => key === tab)) return;
    this._tab = tab;
    this._detailOpen = false;
    this._subview = tab === "delivery" ? "channels" : "general";
  }
  async _tabKey(event, index) {
    let next;
    if (event.key === "ArrowRight") next = (index + 1) % DASHBOARD_TABS.length;
    if (event.key === "ArrowLeft") next = (index + DASHBOARD_TABS.length - 1) % DASHBOARD_TABS.length;
    if (event.key === "Home") next = 0;
    if (event.key === "End") next = DASHBOARD_TABS.length - 1;
    if (next === void 0) return;
    event.preventDefault();
    this._switchTab(DASHBOARD_TABS[next][0]);
    await this.updateComplete;
    this.shadowRoot.querySelectorAll('.dashboard-tabs [role="tab"]')[next]?.focus();
  }
  _icon(icon, tone = "") {
    return b2`<ha-icon class=${tone} .icon=${icon}></ha-icon>`;
  }
  _section(mode, extra = {}) {
    return b2`<herald-dashboard-section .hass=${this.hass} .settings=${{
      ...this._config,
      type: "custom:herald-card",
      view_mode: mode,
      compact: true,
      ...extra
    }}></herald-dashboard-section>`;
  }
  _controlId(key) {
    return this._entityUsable(this._statusEntity()) ? this._data().control_entity_ids?.[key] ?? null : null;
  }
  _quickControl(key, label, icon, tone, description = "") {
    const id = this._controlId(key);
    const entity = this.hass?.states[id];
    const known = this._binaryEntityKnown(entity);
    return b2`<div class="quick-control">
      ${this._icon(icon, tone)}<div><span>${label}</span>${description ? b2`<small>${description}</small>` : A}
      ${!known ? b2`<small>Управление недоступно</small>` : A}${this._renderControlFeedback(id)}</div>
      <ha-switch aria-label=${label} .checked=${known && entity.state === "on"}
        .disabled=${!known || this._controlPending(id)} @change=${() => this._toggleSwitch(id, entity?.state === "on")}></ha-switch>
    </div>`;
  }
  render() {
    if (!this.hass || !this._config) return b2`<div class="loading" role="status">Загружаем Herald…</div>`;
    const status = this._statusEntity();
    const ready = this._entityUsable(status);
    const data = this._data();
    const date = this._now.toLocaleDateString("ru", { weekday: "short", day: "numeric", month: "long" });
    const clock = this._now.toLocaleTimeString("ru", { hour: "2-digit", minute: "2-digit" });
    const homePath = /^\/(?!\/)[^\s]*$/.test(this._config.home_path ?? "") ? this._config.home_path : "/";
    return b2`<main class="dashboard" style=${this._config.fullscreen === true ? "--header-height: 0px" : ""}>
      <header class="dashboard-header"><div class="brand">${this._icon("mdi:bell-badge-outline")}<strong>Herald</strong></div>
        <a class="home-link" href=${homePath}>Главная дома</a><div class="date">${this._icon("mdi:calendar-blank-outline")}<span>${date}</span>${this._icon("mdi:clock-outline")}<time>${clock}</time></div>
      </header>
      ${this._metrics(status, data)}
      <nav class="dashboard-tabs" role="tablist" aria-label="Разделы Herald">${DASHBOARD_TABS.map(([tab, label, icon], index) => b2`
        <button id=${`tab-${tab}`} role="tab" aria-selected=${this._tab === tab} aria-controls="dashboard-content"
          tabindex=${this._tab === tab ? 0 : -1} @click=${() => this._switchTab(tab)} @keydown=${(event) => this._tabKey(event, index)}>
          ${this._icon(icon)}${label}</button>`)}</nav>
      ${!ready ? b2`<p class="availability" role="status">Herald недоступен. Показаны последние данные; управление появится после подключения.</p>` : A}
      <section id="dashboard-content" class=${`workspace ${this._tab === "overview" ? "overview-workspace" : ""}`} role="tabpanel" aria-labelledby=${`tab-${this._tab}`}>
        ${this._tab === "overview" ? this._overview(ready) : !ready ? b2`<p class="empty">Этот раздел появится после подключения Herald.</p>` : this._tab === "rules" ? this._section("policies", { initial_policy_key: this._ruleKey }) : this._tab === "delivery" ? this._delivery() : this._tab === "analytics" ? this._analytics() : this._tab === "controls" ? this._controls() : this._diagnostics()}
      </section>
      <footer>${this._icon("mdi:home-outline")}<span>Тихие часы: ${data.quiet_hours === true ? "\u0432\u043A\u043B\u044E\u0447\u0435\u043D\u044B" : data.quiet_hours === false ? "\u0432\u044B\u043A\u043B\u044E\u0447\u0435\u043D\u044B" : "\u043D\u0435\u0442 \u0434\u0430\u043D\u043D\u044B\u0445"}</span>
        <span>Основная комната: ${this._roomLabel(data.topology?.primary_room)}</span></footer>
      ${this._detailOpen ? this._eventDialog() : A}
    </main>`;
  }
  _metrics(status, data) {
    const ready = this._entityUsable(status);
    const statusLabels = { ready: "\u0413\u043E\u0442\u043E\u0432", idle: "\u0413\u043E\u0442\u043E\u0432", maintenance: "\u041E\u0431\u0441\u043B\u0443\u0436\u0438\u0432\u0430\u043D\u0438\u0435", muted: "\u0422\u0438\u0448\u0438\u043D\u0430", degraded: "\u0422\u0440\u0435\u0431\u0443\u0435\u0442 \u0432\u043D\u0438\u043C\u0430\u043D\u0438\u044F", error: "\u041E\u0448\u0438\u0431\u043A\u0430" };
    const statusLabel = ready ? statusLabels[status.state] ?? this._humanizeCode(status.state) : "\u041D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u0435\u043D";
    const today = this.hass.states[this._config.today_entity];
    const queue = this.hass.states[this._config.queue_entity];
    const analytics = data.analytics ?? {};
    return b2`<div class="metrics">
      <article class="metric metric-status"><div><h2>Herald</h2><strong class=${`status-value ${ready && ["ready", "idle"].includes(status.state) ? "success" : "warning"}`}>${this._icon("mdi:circle", ready && ["ready", "idle"].includes(status.state) ? "success" : "warning")}${statusLabel}</strong><p>Слушает. Обрабатывает.<br>Заботится о важном.</p></div></article>
      <article class="metric metric-events"><h2>События сегодня</h2><strong>${this._icon("mdi:text-box-outline")}${this._entityUsable(today) ? knownCounter(today.state) : "\u2014"}</strong><p>Важное не пропустим</p></article>
      <article class="metric metric-delivery"><h2>Отправки</h2><strong>${this._icon("mdi:send")}${ready ? knownCounter(analytics.deliveries_today) : "\u2014"}</strong><p>Передано сервисам доставки</p></article>
      <article class="metric metric-queue"><h2>Очередь</h2><strong>${this._icon("mdi:timer-sand")}${this._entityUsable(queue) ? knownCounter(queue.state) : "\u2014"}</strong><p>Ошибки: <span class=${Number(analytics.errors_today) > 0 ? "error" : ""}>${ready ? knownCounter(analytics.errors_today) : "\u2014"}</span></p></article>
    </div>`;
  }
  _overview(ready) {
    const item = this._selected();
    const outcome = eventOutcome(item);
    const registry = this._data().notification_registry?.items ?? [];
    const rule = ruleForEvent(item, registry);
    return b2`<div class="overview-grid">
      <article class="hero"><div class="hero-copy">
        <p class="eyebrow">${item ? item === this._events()[0] ? "\u041F\u043E\u0441\u043B\u0435\u0434\u043D\u0435\u0435 \u0441\u043E\u0431\u044B\u0442\u0438\u0435" : "\u0412\u044B\u0431\u0440\u0430\u043D\u043D\u043E\u0435 \u0441\u043E\u0431\u044B\u0442\u0438\u0435" : "\u0421\u043E\u0431\u044B\u0442\u0438\u044F \u0434\u043E\u043C\u0430"}</p>
        <div class="hero-title">${this._icon(item ? eventIcon(item) : "mdi:bell-outline")}<div><h1>${item ? this._friendlyDeliveryItemTitle(item) : "\u0414\u043E\u043C \u043F\u043E\u043A\u0430 \u043C\u043E\u043B\u0447\u0438\u0442"}</h1>
          ${item ? b2`<p class="muted">${this._notificationTime(item.timestamp, true)} · ${this._friendlyFlowName(item.flow ?? "general")} · ${this._friendlyLevelLabel(item.level ?? "info")}</p>` : A}</div></div>
        <p class="hero-message">${item?.message ?? "\u041D\u043E\u0432\u044B\u0435 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F \u043F\u043E\u044F\u0432\u044F\u0442\u0441\u044F \u0437\u0434\u0435\u0441\u044C \u0430\u0432\u0442\u043E\u043C\u0430\u0442\u0438\u0447\u0435\u0441\u043A\u0438."}</p>
        <div class="hero-actions"><span class=${outcome.tone}>${this._icon("mdi:send-outline")}${item ? outcome.label : "\u041E\u0436\u0438\u0434\u0430\u0435\u043C \u043F\u0435\u0440\u0432\u043E\u0435 \u0441\u043E\u0431\u044B\u0442\u0438\u0435"}</span>
          <button class="primary" ?disabled=${!item} @click=${() => this._openEvent()}>Открыть событие ${this._icon("mdi:chevron-right")}</button>
          <button class="secondary" ?disabled=${!rule || !ready} @click=${() => this._openRule(rule)}>Правило доставки</button></div>
      </div></article>
      <aside class="overview-side"><section class="surface events-surface"><div class="surface-heading"><h2>Последние события</h2><button class="icon-button" aria-label="Все события" @click=${() => {
      this._switchTab("diagnostics");
      this._subview = "events";
    }}>${this._icon("mdi:chevron-right")}</button></div>
        <div class="events-list">${this._events().length ? this._events().slice(0, 4).map((event, index) => b2`<button class=${`event-row ${this._selected() === event ? "selected" : ""}`}
          aria-pressed=${this._selected() === event} @click=${() => {
      this._selectedEvent = eventIdentity(event, index);
    }}>
          ${this._icon(eventIcon(event), ["warning", "critical", "security"].includes(event.level) ? "warning" : event.flow === "ai_events" ? "purple" : event.flow === "timer_notifications" ? "timer" : "")}
          <span><strong>${this._friendlyDeliveryItemTitle(event)}</strong><small>${event.message ?? "\u041E\u043F\u0438\u0441\u0430\u043D\u0438\u0435 \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D\u043E"}</small></span><time>${this._notificationTime(event.timestamp, true)}</time></button>`) : b2`<p class="empty">Пока нет событий</p>`}</div>
      </section><section class="surface modes-surface"><h2>Быстрые режимы</h2>
        ${this._quickControl("ai_enabled", "\u0418\u0418-\u043F\u0435\u0440\u0435\u0444\u0440\u0430\u0437\u0438\u0440\u043E\u0432\u0430\u043D\u0438\u0435", "mdi:auto-fix", "purple", "\u0411\u043E\u043B\u0435\u0435 \u0435\u0441\u0442\u0435\u0441\u0442\u0432\u0435\u043D\u043D\u044B\u0435 \u0443\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F")}
        ${this._quickControl("mute_all", "\u0413\u043B\u043E\u0431\u0430\u043B\u044C\u043D\u0430\u044F \u0442\u0438\u0448\u0438\u043D\u0430", "mdi:bell-off-outline", "", "\u041E\u0431\u044B\u0447\u043D\u044B\u0435 \u0441\u043E\u0431\u044B\u0442\u0438\u044F \u043E\u0442\u043A\u043B\u044E\u0447\u0435\u043D\u044B; \u043A\u0440\u0438\u0442\u0438\u0447\u0435\u0441\u043A\u0438\u0435 \u043C\u043E\u0433\u0443\u0442 \u043F\u0440\u043E\u0445\u043E\u0434\u0438\u0442\u044C")}
        ${this._quickControl("maintenance_mode", "\u041E\u0431\u0441\u043B\u0443\u0436\u0438\u0432\u0430\u043D\u0438\u0435", "mdi:wrench", "warning", "\u0423\u0432\u0435\u0434\u043E\u043C\u043B\u0435\u043D\u0438\u044F HA \u0438 \u0441\u0438\u0441\u0442\u0435\u043C\u043D\u044B\u0439 \u0436\u0443\u0440\u043D\u0430\u043B")}
      </section></aside>
    </div>`;
  }
  _roomLabel(room) {
    if (!room) return "\u043D\u0435 \u043E\u043F\u0440\u0435\u0434\u0435\u043B\u0435\u043D\u0430";
    return this._data().topology?.rooms?.find((item) => item.room === room)?.label ?? this._friendlyRoomLabel(room);
  }
  _openRule(rule) {
    if (!rule?.notification_key) return;
    this._ruleKey = rule.notification_key;
    this._switchTab("rules");
  }
  async _openEvent() {
    if (!this._selected()) return;
    this._eventFeedback = "";
    this._detailOpen = true;
    await this.updateComplete;
    this.shadowRoot.querySelector("dialog")?.showModal();
  }
  _eventDialog() {
    const item = this._selected();
    const rule = ruleForEvent(item, this._data().notification_registry?.items ?? []);
    return b2`<dialog aria-labelledby="event-title" @close=${() => {
      this._detailOpen = false;
    }}>
      <div class="surface-heading"><h2 id="event-title">${this._friendlyDeliveryItemTitle(item)}</h2><button class="icon-button" aria-label="Закрыть событие" @click=${() => this.shadowRoot.querySelector("dialog").close()}>${this._icon("mdi:close")}</button></div>
      <p class="muted">${this._notificationTime(item.timestamp)} · ${this._friendlyLevelLabel(item.level ?? "info")}</p><p class="full-message">${item.message ?? "\u041E\u043F\u0438\u0441\u0430\u043D\u0438\u0435 \u043D\u0435 \u0443\u043A\u0430\u0437\u0430\u043D\u043E"}</p>
      ${item.explanation ? this._renderPolicyExplanation({ explanation: item.explanation }) : b2`<p class="muted">Для этого события подробное объяснение не сохранено.</p>`}
      <h3>Результаты отправки</h3>${item.results?.length ? b2`<ul class="plain-list">${item.results.map((result) => b2`<li>${this._friendlyChannelName(result.channel)}<strong class=${result.status === "error" ? "error" : result.status === "sent" ? "success" : "muted"}>${{ sent: "\u041E\u0442\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u043E", error: "\u041E\u0448\u0438\u0431\u043A\u0430", dropped: "\u041F\u0440\u043E\u043F\u0443\u0449\u0435\u043D\u043E" }[result.status] ?? "\u041D\u0435\u0442 \u0440\u0435\u0437\u0443\u043B\u044C\u0442\u0430\u0442\u0430"}</strong></li>`)}</ul>` : b2`<p class="muted">Нет сохранённых результатов</p>`}
      <p class="muted">Отправка в сервис не подтверждает получение или прочтение на устройстве.</p>
      <div class="dialog-actions"><button class="primary" ?disabled=${!rule} @click=${() => this._openRule(rule)}>Открыть правило</button>
        <button class="secondary" ?disabled=${!item.notification_id || item.acknowledged || this._eventBusy} @click=${() => this._acknowledge(item)}>${item.acknowledged ? "\u041E\u0442\u043C\u0435\u0447\u0435\u043D\u043E \u043F\u0440\u043E\u0447\u0438\u0442\u0430\u043D\u043D\u044B\u043C" : this._eventBusy ? "\u0421\u043E\u0445\u0440\u0430\u043D\u044F\u0435\u043C\u2026" : "\u041E\u0442\u043C\u0435\u0442\u0438\u0442\u044C \u043F\u0440\u043E\u0447\u0438\u0442\u0430\u043D\u043D\u044B\u043C"}</button></div>
      ${this._eventFeedback ? b2`<p role="status">${this._eventFeedback}</p>` : A}
    </dialog>`;
  }
  async _acknowledge(item) {
    if (!item?.notification_id || this._eventBusy) return;
    this._eventBusy = true;
    try {
      await this.hass.callService("herald", "acknowledge", { notification_id: item.notification_id, ...this._entryScope() });
      this._eventFeedback = "\u041A\u043E\u043C\u0430\u043D\u0434\u0430 \u043F\u0440\u0438\u043D\u044F\u0442\u0430. \u041E\u0436\u0438\u0434\u0430\u0435\u043C \u043F\u043E\u0434\u0442\u0432\u0435\u0440\u0436\u0434\u0435\u043D\u0438\u0435 \u0432 \u0441\u043E\u0431\u044B\u0442\u0438\u0438.";
    } catch (error) {
      this._eventFeedback = this._policyError(error);
    } finally {
      this._eventBusy = false;
    }
  }
  _entryScope() {
    return this._config.entry_id ? { entry_id: this._config.entry_id } : {};
  }
  _subnav(items) {
    return b2`<nav class="subnav" aria-label="Подраздел">${items.map(([key, label]) => b2`<button class=${this._subview === key ? "active" : ""} aria-pressed=${this._subview === key} @click=${() => {
      this._subview = key;
    }}>${label}</button>`)}</nav>`;
  }
  _delivery() {
    return b2`${this._subnav([["channels", "\u041A\u0430\u043D\u0430\u043B\u044B"], ["rooms", "\u041A\u043E\u043C\u043D\u0430\u0442\u044B"], ["users", "\u041F\u043E\u043B\u0443\u0447\u0430\u0442\u0435\u043B\u0438"]])}
      ${this._subview === "rooms" ? b2`<h2>Доставка по комнатам</h2><div class="room-grid">${(this._data().topology?.rooms ?? []).map((room) => b2`<section class="surface"><div class="surface-heading"><h3>${room.label ?? this._roomLabel(room.room)}</h3>${this._icon("mdi:home-account")}</div>
        <p class="muted">${room.primary ? "\u041E\u0441\u043D\u043E\u0432\u043D\u0430\u044F \u043A\u043E\u043C\u043D\u0430\u0442\u0430 \xB7 " : ""}${this._friendlyBinaryState(this.hass.states[room.presence_entity]?.state)}</p>
        ${this._controlRow(this._controlId(`room_presence:${room.room}`), "\u0420\u0443\u0447\u043D\u043E\u0435 \u043F\u0440\u0438\u0441\u0443\u0442\u0441\u0442\u0432\u0438\u0435", "mdi:account-outline")}
        ${this._controlId(`room_audio_target:${room.room}`) ? this._controlRow(this._controlId(`room_audio_target:${room.room}`), "\u0423\u0441\u0442\u0440\u043E\u0439\u0441\u0442\u0432\u043E \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0438", "mdi:speaker") : A}
        <ul class="plain-list">${[...room.voice_targets ?? [], ...room.tv_targets ?? []].map((target) => b2`<li>${this.hass.states[target.entity_id]?.attributes.friendly_name ?? this._friendlyChannelName(target.channel)}<small>${target.available ? "\u0415\u0441\u0442\u044C \u0432 HA" : "\u041D\u0435\u0434\u043E\u0441\u0442\u0443\u043F\u043D\u043E"}</small></li>`)}</ul>
        ${!room.voice_targets?.length && !room.tv_targets?.length ? b2`<p class="muted">Цели доставки не найдены</p>` : A}</section>`)}</div>` : this._subview === "users" ? this._users() : b2`${this._renderConfigurationOverview()}${this._renderChannels()}`}`;
  }
  _analytics() {
    const data = this._data().analytics ?? {};
    return b2`<h2>Аналитика Herald</h2><div class="counter-row">${[["\u041E\u0442\u043F\u0440\u0430\u0432\u043A\u0438", data.deliveries_today], ["\u041F\u0440\u043E\u043F\u0443\u0441\u043A\u0438", data.dropped_today], ["\u041E\u0448\u0438\u0431\u043A\u0438", data.errors_today], ["\u0418\u0418-\u0437\u0430\u043F\u0440\u043E\u0441\u044B", data.ai_requests_today]].map(([label, value]) => b2`<div><span>${label} сегодня</span><strong>${knownCounter(value)}</strong></div>`)}</div>
      <div class="analytics-grid">${this._distribution("\u041E\u0442\u043F\u0440\u0430\u0432\u043A\u0438 \u043F\u043E \u043A\u0430\u043D\u0430\u043B\u0430\u043C", data.channel_delivery_counts, (name) => this._friendlyChannelName(name))}${this._distribution("\u041E\u0448\u0438\u0431\u043A\u0438 \u043F\u043E \u043A\u0430\u043D\u0430\u043B\u0430\u043C", data.channel_error_counts, (name) => this._friendlyChannelName(name))}
      ${this._distribution("\u041F\u0440\u0438\u0447\u0438\u043D\u044B \u043F\u0440\u043E\u043F\u0443\u0441\u043A\u043E\u0432", data.drop_reasons, (name) => this._humanizeCode(name))}${this._distribution("\u0418\u0418-\u043F\u0435\u0440\u0441\u043E\u043D\u0430\u0436\u0438", data.ai_character_counts, (name) => this._friendlyCharacterName(name))}</div>
      <p class="muted">Распределение по сохранённым счётчикам Herald. История по часам пока не собирается.</p>`;
  }
  _distribution(title, values, label) {
    const entries = Object.entries(values ?? {}).filter(([, value]) => Number.isFinite(Number(value)) && Number(value) >= 0).sort((a3, b3) => b3[1] - a3[1]);
    const max = Math.max(1, ...entries.map(([, value]) => Number(value)));
    return b2`<section class="surface"><h3>${title}</h3>${entries.length ? b2`<ul class="distribution">${entries.map(([name, value]) => b2`<li><span>${label(name)}</span><meter min="0" max=${max} value=${value} aria-label=${label(name)}></meter><strong>${value}</strong></li>`)}</ul>` : b2`<p class="empty">Данных пока нет</p>`}</section>`;
  }
  _users() {
    const users = this._data().topology?.users ?? [];
    return b2`<h2>Получатели</h2><div class="room-grid">${users.map((user) => b2`<section class="surface"><h3>${user.name}</h3><p class="muted">${user.home ? "\u0414\u043E\u043C\u0430" : "\u041D\u0435 \u0434\u043E\u043C\u0430"}</p>
      ${this._controlRow(this._controlId(`user_language:${user.slug}`), "\u042F\u0437\u044B\u043A", "mdi:translate")}
      ${this._controlRow(this._controlId(`user_character:${user.slug}`), "\u041F\u0435\u0440\u0441\u043E\u043D\u0430\u0436", "mdi:account-star-outline")}
      ${this._controlRow(this._controlId(`user_silent:${user.slug}`), "\u0411\u0435\u0437 \u0437\u0432\u0443\u043A\u0430", "mdi:bell-off-outline")}</section>`)}</div>`;
  }
  _controls() {
    const data = this._data();
    return b2`${this._subnav([["general", "\u041E\u0431\u0449\u0435\u0435"], ["flows", "\u041F\u043E\u0442\u043E\u043A\u0438"], ["users", "\u041F\u043E\u043B\u044C\u0437\u043E\u0432\u0430\u0442\u0435\u043B\u0438"], ["ai", "\u0418\u0418 \u0438 \u043F\u0435\u0440\u0441\u043E\u043D\u0430\u0436\u0438"]])}
      ${this._subview === "users" ? this._users() : this._subview === "flows" ? b2`<h2>Потоки уведомлений</h2><div class="room-grid">${Object.entries(data.flow_policies ?? {}).map(([flow]) => b2`<section class="surface"><h3>${this._friendlyFlowName(flow)}</h3>
        ${[["flow_enabled", "\u0412\u043A\u043B\u044E\u0447\u0451\u043D", "mdi:source-branch"], ["flow_summary_window", "\u041E\u043A\u043D\u043E \u0441\u0432\u043E\u0434\u043A\u0438, \u0441", "mdi:timer-outline"], ["flow_dedup_window", "\u0417\u0430\u0449\u0438\u0442\u0430 \u043E\u0442 \u043F\u043E\u0432\u0442\u043E\u0440\u043E\u0432, \u0441", "mdi:content-copy"], ["flow_cooldown", "\u041F\u0430\u0443\u0437\u0430 \u0434\u043E\u0441\u0442\u0430\u0432\u043A\u0438, \u0441", "mdi:pause"]].map(([key, label, icon]) => this._controlRow(this._controlId(`${key}:${flow}`), label, icon))}
        ${this._renderFlow(flow, data.flow_states?.[flow], data.snoozed_flows?.[flow])}</section>`)}</div>${this._section("queue")}` : this._subview === "ai" ? b2`<h2>ИИ и персонажи</h2><div class="surface">${this._quickControl("ai_enabled", "\u0418\u0418-\u043F\u0435\u0440\u0435\u0444\u0440\u0430\u0437\u0438\u0440\u043E\u0432\u0430\u043D\u0438\u0435", "mdi:auto-fix", "purple")}
          ${["info", "warning", "critical"].map((level) => this._controlRow(this._controlId(`ai_level:${level}`), this._friendlyLevelLabel(level), "mdi:brain"))}
          <p class="muted">Сервер, модель и голос настраиваются в параметрах интеграции.</p><a class="secondary settings-link" href="/config/integrations/integration/herald">Параметры Herald</a></div>${this._section("characters")}` : b2`<h2>Общие настройки</h2><div class="analytics-grid"><section class="surface"><h3>Режимы</h3>
          ${this._quickControl("mute_all", "\u0413\u043B\u043E\u0431\u0430\u043B\u044C\u043D\u0430\u044F \u0442\u0438\u0448\u0438\u043D\u0430", "mdi:bell-off-outline", "")}${this._quickControl("maintenance_mode", "\u041E\u0431\u0441\u043B\u0443\u0436\u0438\u0432\u0430\u043D\u0438\u0435", "mdi:wrench", "warning")}
          ${this._controlRow(this._controlId("maintenance_min_level"), "\u0412\u0430\u0436\u043D\u043E\u0441\u0442\u044C \u0432 \u043E\u0431\u0441\u043B\u0443\u0436\u0438\u0432\u0430\u043D\u0438\u0438", "mdi:alert-outline")}${this._quickControl("dashboard_sidebar", "\u041F\u043E\u043A\u0430\u0437\u044B\u0432\u0430\u0442\u044C \u0432 \u043C\u0435\u043D\u044E", "mdi:view-dashboard", "")}</section>
          <section class="surface"><h3>Важность и способы доставки</h3>${["info", "warning", "critical"].map((level) => this._controlRow(this._controlId(`level_enabled:${level}`), this._friendlyLevelLabel(level), "mdi:bell-outline"))}
          ${["voice", "push", "tv"].map((family) => this._controlRow(this._controlId(`channel_family:${family}`), this._friendlyChannelFamilyLabel(family), "mdi:send-outline"))}</section></div>`}`;
  }
  _controlRow(id, label, icon) {
    const entity = this.hass.states[id];
    const known = this._entityUsable(entity);
    const domain = String(id ?? "").split(".")[0];
    return b2`<div class="control-row">${this._icon(entity?.attributes.icon ?? icon)}<label for=${id ?? label}>${label}</label>
      ${domain === "switch" ? b2`<ha-switch aria-label=${label} .checked=${known && entity.state === "on"} .disabled=${!this._binaryEntityKnown(entity) || this._controlPending(id)} @change=${() => this._toggleSwitch(id, entity.state === "on")}></ha-switch>` : domain === "select" ? b2`<select id=${id} aria-label=${label} .value=${known ? entity.state : ""} ?disabled=${!known || this._controlPending(id)} @change=${(event) => this._setSelectOption(id, event)}>
      ${known ? (entity.attributes.options ?? []).map((value) => b2`<option value=${value} .selected=${entity.state === value}>${value}</option>`) : b2`<option value="">Недоступно</option>`}</select>` : domain === "number" ? b2`<input id=${id} type="number" aria-label=${label} .value=${known ? entity.state : ""} min=${entity?.attributes.min ?? 0} max=${entity?.attributes.max ?? 86400} step=${entity?.attributes.step ?? 1} ?disabled=${!known || this._controlPending(id)} @change=${(event) => this._setNumber(id, event)}>` : b2`<span class="muted">Недоступно</span>`}
      <div class="control-feedback">${this._numberErrors[id] ? b2`<p class="error" role="alert">${this._numberErrors[id]}</p>` : this._renderControlFeedback(id)}</div></div>`;
  }
  async _setNumber(id, event) {
    const entity = this.hass.states[id];
    const input = event.target;
    const value = Number(input.value);
    if (!id?.startsWith("number.") || !this._entityUsable(entity) || input.value === "" || !Number.isFinite(value) || value < Number(entity.attributes.min ?? 0) || value > Number(entity.attributes.max ?? 86400) || input.validity?.valid === false) {
      this._numberErrors = { ...this._numberErrors, [id]: "\u0417\u043D\u0430\u0447\u0435\u043D\u0438\u0435 \u0432\u043D\u0435 \u0434\u043E\u043F\u0443\u0441\u0442\u0438\u043C\u043E\u0433\u043E \u0434\u0438\u0430\u043F\u0430\u0437\u043E\u043D\u0430" };
      input.value = entity?.state ?? "";
      return;
    }
    this._numberErrors = { ...this._numberErrors, [id]: void 0 };
    input.value = entity.state;
    await this._runControlAction(id, String(value), "number", "set_value", { entity_id: id, value });
  }
  _diagnostics() {
    const data = this._data();
    return b2`${this._subnav([["general", "\u041D\u0430\u0441\u0442\u0440\u043E\u0439\u043A\u0438 \u0438 \u0441\u043E\u0441\u0442\u043E\u044F\u043D\u0438\u0435"], ["events", "\u0412\u0441\u0435 \u0441\u043E\u0431\u044B\u0442\u0438\u044F"], ["trace", "\u042D\u0442\u0430\u043F\u044B \u043E\u0431\u0440\u0430\u0431\u043E\u0442\u043A\u0438"]])}
      ${this._subview === "events" ? b2`<h2>История событий</h2><div class="history-list">${this._events().map((item, index) => b2`<button class="event-row" @click=${() => {
      this._selectedEvent = eventIdentity(item, index);
      this._openEvent();
    }}>${this._icon(eventIcon(item))}<span><strong>${this._friendlyDeliveryItemTitle(item)}</strong><small>${item.message}</small></span><time>${this._notificationTime(item.timestamp)}</time></button>`)}</div>` : this._subview === "trace" ? b2`<h2>Последние этапы обработки</h2><ul class="trace-list">${(data.pipeline_trace ?? []).map((stage) => b2`<li><time>${this._notificationTime(stage.timestamp, true)}</time><strong>${this._humanizeCode(stage.stage)}</strong><span>${stage.status ? this._humanizeCode(stage.status) : stage.event ?? ""}</span></li>`)}</ul><h3>Последняя проверка маршрута</h3>${data.last_route_preview?.explanation ? this._renderPolicyExplanation(data.last_route_preview) : b2`<p class="muted">Предпросмотр ещё не выполнялся</p>`}` : b2`<h2>Диагностика</h2>${this._renderConfigurationOverview()}${this._section("queue")}
        <section class="surface"><h3>Проверка доставки</h3><p class="muted">Откройте тестовую сущность в Home Assistant. Её кнопка отправляет реальное уведомление.</p>
        <div class="test-actions">${(data.control_entities?.tests ?? []).filter((id) => this.hass.states[id]).map((id) => b2`<button class="secondary" @click=${() => this._openSetting(id)}>${this.hass.states[id].attributes.friendly_name ?? "\u041F\u0440\u043E\u0432\u0435\u0440\u043A\u0430 \u043A\u0430\u043D\u0430\u043B\u0430"} ${this._icon("mdi:open-in-new")}</button>`)}</div></section>`}`;
  }
};
__publicField(HeraldDashboard, "properties", {
  _tab: { state: true },
  _selectedEvent: { state: true },
  _detailOpen: { state: true },
  _subview: { state: true },
  _ruleKey: { state: true },
  _now: { state: true },
  _numberErrors: { state: true },
  _eventFeedback: { state: true },
  _eventBusy: { state: true }
});
__publicField(HeraldDashboard, "styles", [HeraldCard.styles, i`
    :host { display: block; --primary-text-color: #d9edf4; --secondary-text-color: #93b7c6; --primary-color: #43c4e9; --ha-card-background: #082631; color: #d9edf4; font-family: var(--paper-font-body1_-_font-family, Roboto, sans-serif); }
    * { box-sizing: border-box; }
    .dashboard { background: #082631; height: calc(100dvh - var(--header-height, 56px)); min-height: 0; padding: 16px 22px 12px; display: flex; flex-direction: column; gap: 14px; }
    .dashboard-header { display: flex; align-items: center; gap: 26px; min-height: 44px; }
    .brand { display: flex; align-items: center; gap: 12px; font-size: 28px; }
    .brand ha-icon { --mdc-icon-size: 38px; }
    .home-link { border-left: 1px solid #245060; padding-left: 26px; }
    a { color: #d9edf4; text-decoration: none; }
    a:hover { color: #43c4e9; }
    .date { margin-left: auto; display: flex; align-items: center; gap: 12px; font-size: 15px; }
    .metrics { display: grid; grid-template-columns: repeat(4, minmax(0, 1fr)); gap: 10px; }
    .metric { background-size: cover; background-position: center; height: clamp(140px, 18dvh, 216px); border: 1px solid #376272; border-radius: 10px; padding: 22px 30px; display: flex; flex-direction: column; justify-content: center; }
    .metric h2 { font-size: 20px; max-width: 180px; margin: 0 0 12px; }
    .metric strong { font-size: 42px; display: flex; align-items: center; gap: 12px; }
    .metric strong ha-icon { --mdc-icon-size: 36px; }
    .metric p { font-size: 13px; line-height: 1.5; margin: 8px 0 0; color: #b0cbd7; }
    .metric-status { background-image: url('/herald/assets/herald-status.webp'); padding-left: 42%; }
    .metric-status h2 { font-size: 22px; }
    .metric .status-value { font-size: 24px; gap: 10px; }
    .metric .status-value ha-icon { --mdc-icon-size: 20px; }
    .metric-events { background-image: url('/herald/assets/herald-events.webp'); }
    .metric-delivery { background-image: url('/herald/assets/herald-delivery.webp'); }
    .metric-queue { background-image: url('/herald/assets/herald-queue.webp'); }
    ha-icon { color: #43c4e9; flex-shrink: 0; --mdc-icon-size: 24px; }
    .success, ha-icon.success { color: #43dca0; } .warning, ha-icon.warning { color: #ffc65b; } .error { color: #ff7979; } .purple, ha-icon.purple { color: #b17aff; } .timer, ha-icon.timer { color: #eaa385; } .muted { color: #93b7c6; }
    .dashboard-tabs { display: flex; border-bottom: 1px solid #245060; gap: 10px; flex-shrink: 0; overflow-x: auto; }
    .dashboard-tabs button { flex: 1; display: flex; align-items: center; justify-content: center; gap: 13px; padding: 12px 8px 15px; border: 0; border-bottom: 3px solid transparent; border-radius: 0; background: none; color: #93b7c6; white-space: nowrap; font-size: 16px; }
    .dashboard-tabs button[aria-selected='true'] { border-bottom-color: #43c4e9; color: #edfaff; font-weight: 600; }
    button { font: inherit; cursor: pointer; color: inherit; }
    button:hover:not(:disabled) { filter: brightness(1.14); }
    button:focus-visible, a:focus-visible, input:focus-visible, select:focus-visible { outline: 2px solid #cceffa; outline-offset: 3px; }
    button:disabled { opacity: .5; cursor: not-allowed; }
    .workspace { background: #082631; flex: 1; min-height: 0; }
    .workspace:not(.overview-workspace) { max-height: calc(100dvh - 350px); overflow: auto; padding: 12px 6px; scrollbar-color: #346174 #082631; }
    .overview-grid { display: grid; grid-template-columns: minmax(0, 2fr) minmax(340px, 1fr); gap: 14px; min-height: 0; height: 100%; }
    .hero { background-image: url('/herald/assets/herald-hero.webp'); background-size: cover; background-position: center; position: relative; border-radius: 10px; border: 1px solid #245060; overflow: hidden; display: flex; align-items: flex-end; }
    .hero-copy { padding: 25px 32px; width: 100%; background: rgba(3, 25, 34, .85); }
    .eyebrow { text-transform: none; letter-spacing: 0; font-size: 16px; color: #a1c7d7; margin: 0 0 16px; }
    .hero-title { display: flex; gap: 20px; align-items: center; }
    .hero-title > ha-icon { --mdc-icon-size: 42px; }
    h1 { font-size: 27px; line-height: 1.18; margin: 0 0 8px; }
    h2 { font-size: 20px; margin: 0 0 18px; } h3 { font-size: 18px; margin: 0 0 15px; }
    .hero-title p { font-size: 14px; margin: 0; }
    .hero-message { font-size: 16px; line-height: 1.5; max-height: 100px; overflow: auto; margin: 18px 0; white-space: pre-wrap; overflow-wrap: anywhere; }
    .hero-actions { border-top: 1px solid #245060; padding-top: 15px; display: flex; gap: 12px; align-items: center; flex-wrap: wrap; }
    .hero-actions > span { display: flex; align-items: center; gap: 10px; font-size: 13px; margin-right: auto; }
    .primary, .secondary { display: inline-flex; align-items: center; justify-content: center; gap: 10px; padding: 13px 18px; border-radius: 10px; font-size: 14px; min-height: 44px; }
    .primary { background: #43c4e9; color: #002430; border: 1px solid #43c4e9; font-weight: 600; }
    .primary ha-icon { color: #002430; }
    .secondary { background: #072732; color: #d9edf4; border: 1px solid #3e758c; }
    .overview-side { display: grid; grid-template-rows: minmax(0, 1.15fr) minmax(220px, .85fr); gap: 14px; min-height: 0; }
    .surface { background: #092a36; border: 1px solid #245060; border-radius: 12px; padding: 22px 24px; }
    .surface-heading { display: flex; align-items: center; justify-content: space-between; gap: 16px; }
    .surface-heading h2, .surface-heading h3 { margin: 0; }
    .icon-button { border: 0; background: transparent; padding: 8px; display: inline-flex; }
    .events-surface { padding: 14px 10px; display: flex; flex-direction: column; min-height: 0; }
    .events-surface .surface-heading { padding: 0 12px 12px; }
    .events-list { min-height: 0; overflow: auto; }
    .event-row { display: flex; align-items: center; gap: 16px; width: 100%; text-align: left; background: transparent; padding: 17px 14px; border: 0; border-bottom: 1px solid #245060; border-radius: 0; }
    .event-row:last-child { border-bottom: 0; }
    .event-row.selected { background: #10394a; border-radius: 9px; }
    .event-row > ha-icon { --mdc-icon-size: 32px; }
    .event-row > span { flex: 1; min-width: 0; }
    .event-row strong { font-size: 14px; font-weight: 500; line-height: 1.4; display: block; }
    .event-row small { font-size: 12px; color: #93b7c6; display: -webkit-box; -webkit-line-clamp: 2; -webkit-box-orient: vertical; overflow: hidden; margin-top: 6px; line-height: 1.4; overflow-wrap: anywhere; }
    .event-row time { font-size: 12px; align-self: flex-start; padding-top: 4px; color: #afceda; }
    .quick-control { display: flex; align-items: center; gap: 16px; padding: 17px 0; border-bottom: 1px solid #245060; }
    .quick-control:last-child { border-bottom: 0; padding-bottom: 0; }
    .quick-control > ha-icon { --mdc-icon-size: 29px; }
    .quick-control > div { flex: 1; min-width: 0; font-size: 14px; }
    .quick-control small { display: block; color: #93b7c6; font-size: 11px; line-height: 1.45; margin-top: 6px; }
    ha-switch { --switch-checked-button-color: #e8f8ff; --switch-checked-track-color: #43c4e9; --switch-unchecked-button-color: #d9edf4; --switch-unchecked-track-color: #547484; }
    .modes-surface { padding: 20px 24px; overflow: auto; }
    footer { display: flex; justify-content: flex-start; align-items: center; gap: 16px; color: #93b7c6; font-size: 12px; min-height: 25px; flex-wrap: wrap; }
    .subnav { display: flex; gap: 8px; margin-bottom: 22px; overflow: auto; }
    .subnav button { border: 0; border-radius: 8px; background: transparent; padding: 10px 18px; white-space: nowrap; color: #93b7c6; }
    .subnav button.active { background: #164455; color: #edfaff; }
    .analytics-grid, .room-grid { display: grid; grid-template-columns: repeat(2, minmax(0, 1fr)); gap: 18px; margin: 18px 0; }
    .counter-row { display: grid; grid-template-columns: repeat(4, 1fr); gap: 25px; padding: 20px 0 35px; }
    .counter-row span { display: block; color: #93b7c6; } .counter-row strong { display: block; font-size: 32px; margin-top: 12px; }
    .plain-list, .distribution, .trace-list { list-style: none; padding: 0; margin: 20px 0; }
    .plain-list li { display: flex; justify-content: space-between; padding: 12px 0; gap: 20px; border-bottom: 1px solid #245060; }
    .distribution li { display: grid; grid-template-columns: minmax(0, 1fr) 110px 35px; align-items: center; gap: 14px; padding: 13px 0; }
    meter { width: 100%; accent-color: #43c4e9; }
    .control-row { display: grid; grid-template-columns: 24px minmax(0, 1fr) auto; align-items: center; gap: 12px; border-bottom: 1px solid #245060; padding: 14px 0; }
    .control-feedback { grid-column: 2 / 4; }
    .control-feedback:empty { display: none; }
    input, select { color-scheme: dark; background: #0c3342; color: #d9edf4; border: 1px solid #346174; border-radius: 8px; padding: 10px; font: inherit; max-width: 190px; }
    input[type=number] { width: 100px; }
    .trace-list li { display: grid; grid-template-columns: 80px minmax(150px, 1fr) 2fr; gap: 20px; padding: 15px 0; border-bottom: 1px solid #245060; }
    .test-actions { display: flex; flex-wrap: wrap; gap: 12px; }
    .availability { color: #ffc65b; margin: 0; }
    .history-list .event-row small { -webkit-line-clamp: 3; }
    dialog { color: #d9edf4; background: #082631; border: 1px solid #43c4e9; border-radius: 18px; padding: 25px; width: min(850px, calc(100vw - 32px)); max-height: 85dvh; overflow: auto; }
    dialog::backdrop { background: rgba(1, 15, 22, .8); backdrop-filter: blur(7px); }
    .full-message { white-space: pre-wrap; line-height: 1.6; overflow-wrap: anywhere; }
    .dialog-actions { display: flex; gap: 12px; flex-wrap: wrap; }
    @media (min-width: 1100px) and (max-height: 850px) { .dashboard { gap: 10px; } .metric { height: 138px; padding-top: 14px; padding-bottom: 14px; } .metric h2 { font-size: 16px; margin-bottom: 8px; } .metric strong { font-size: 30px; } .metric p { font-size: 11px; } .overview-grid { height: 100%; min-height: 0; } .hero-copy { padding: 18px 22px; } .hero-title h1 { font-size: 22px; } .overview-side { grid-template-rows: 1.1fr .9fr; } .event-row { padding: 10px; } .quick-control { padding: 10px 0; } .modes-surface { padding: 15px 20px; } .quick-control small { font-size: 10px; } .workspace:not(.overview-workspace) { max-height: calc(100dvh - 300px); } }
    @media (max-width: 1050px) { .dashboard { padding: 14px; } .metric { padding: 18px; } .metric-status { padding-left: 36%; } .metric h2 { font-size: 17px; } .metric .status-value { font-size: 20px; } .overview-grid { grid-template-columns: minmax(0, 1.4fr) minmax(290px, 1fr); } .hero-actions { gap: 10px; } .hero-actions > span { width: 100%; } .hero-copy { padding: 22px; } .hero-title { gap: 12px; } h1 { font-size: 22px; } .dashboard-tabs { gap: 0; } .dashboard-tabs button { gap: 7px; font-size: 14px; } .date { font-size: 13px; } }
    @media (min-width: 761px) and (max-width: 1100px) { .overview-grid { grid-template-columns: minmax(0, 2fr) minmax(300px, 1fr); } .surface-heading h2 { font-size: 17px; } .event-row { padding: 10px; gap: 10px; } .event-row strong { font-size: 12px; } .event-row small { font-size: 10px; margin-top: 4px; } .event-row time { font-size: 10px; } .event-row > ha-icon { --mdc-icon-size: 26px; } .quick-control { padding: 10px 0; gap: 10px; } .quick-control > div { font-size: 12px; } .quick-control small { font-size: 10px; margin-top: 4px; } .modes-surface { padding: 15px 18px; } .events-surface .surface-heading { padding-bottom: 8px; } }
    @media (min-width: 761px) and (max-height: 1000px) { .dashboard { gap: 10px; } .dashboard-header { min-height: 38px; } .overview-side { grid-template-rows: minmax(0, 1fr) auto; } .event-row { padding-top: 8px; padding-bottom: 8px; } .quick-control { padding-top: 8px; padding-bottom: 8px; } .modes-surface { padding-top: 12px; padding-bottom: 12px; } .metric { height: clamp(138px, 17dvh, 170px); } footer { min-height: 20px; } }
    @media (max-width: 760px) { .dashboard { gap: 12px; height: auto; min-height: auto; } .dashboard-header { flex-wrap: wrap; gap: 15px; } .brand { font-size: 24px; } .home-link { padding-left: 15px; font-size: 14px; } .date { width: 100%; margin: 0; justify-content: flex-end; } .metrics { grid-template-columns: repeat(2, minmax(0, 1fr)); } .metric { height: 150px; } .metric-status { padding-left: 42%; } .dashboard-tabs button { min-width: 110px; } .overview-grid { display: flex; flex-direction: column; height: auto; min-height: 0; } .hero { min-height: 570px; } .hero-copy { margin-top: 280px; } .hero-actions > span { width: 100%; } .overview-side { display: flex; flex-direction: column; } .events-list { max-height: 390px; } .workspace:not(.overview-workspace) { max-height: none; overflow: visible; } .analytics-grid, .room-grid { grid-template-columns: 1fr; } .counter-row { grid-template-columns: repeat(2, 1fr); } footer { font-size: 11px; } .control-row { grid-template-columns: 24px minmax(0, 1fr); } .control-row > select, .control-row > input, .control-row > ha-switch { grid-column: 2; justify-self: start; } .control-feedback { grid-column: 2; } }
    @media (prefers-reduced-motion: reduce) { *, *::before, *::after { transition: none !important; animation: none !important; } }
  `]);
if (!customElements.get("herald-dashboard-section")) customElements.define("herald-dashboard-section", HeraldDashboardSection);
if (!customElements.get("ha-herald-dashboard")) customElements.define("ha-herald-dashboard", HeraldDashboard);
if (!window.customCards.some((item) => item.type === "ha-herald-dashboard")) window.customCards.push({ type: "ha-herald-dashboard", name: "Herald: \u0414\u0430\u0448\u0431\u043E\u0440\u0434", description: "\u041E\u0431\u0437\u043E\u0440 \u0438 \u0443\u043F\u0440\u0430\u0432\u043B\u0435\u043D\u0438\u0435 Herald", preview: true, documentationURL: "https://github.com/Mesteriis/ha-herald" });
/*! Bundled license information:

@lit/reactive-element/css-tag.js:
  (**
   * @license
   * Copyright 2019 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

@lit/reactive-element/reactive-element.js:
lit-html/lit-html.js:
lit-element/lit-element.js:
  (**
   * @license
   * Copyright 2017 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)

lit-html/is-server.js:
  (**
   * @license
   * Copyright 2022 Google LLC
   * SPDX-License-Identifier: BSD-3-Clause
   *)
*/
