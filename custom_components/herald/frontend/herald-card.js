var __defProp = Object.defineProperty;
var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
var __decorateClass = (decorators, target, key, kind) => {
  var result = kind > 1 ? void 0 : kind ? __getOwnPropDesc(target, key) : target;
  for (var i5 = decorators.length - 1, decorator; i5 >= 0; i5--)
    if (decorator = decorators[i5])
      result = (kind ? decorator(target, key, result) : decorator(result)) || result;
  if (kind && result) __defProp(target, key, result);
  return result;
};

// node_modules/@lit/reactive-element/css-tag.js
var t = globalThis;
var e = t.ShadowRoot && (void 0 === t.ShadyCSS || t.ShadyCSS.nativeShadow) && "adoptedStyleSheets" in Document.prototype && "replace" in CSSStyleSheet.prototype;
var s = Symbol();
var o = /* @__PURE__ */ new WeakMap();
var n = class {
  constructor(t4, e5, o6) {
    if (this._$cssResult$ = true, o6 !== s) throw Error("CSSResult is not constructable. Use `unsafeCSS` or `css` instead.");
    this.cssText = t4, this.t = e5;
  }
  get styleSheet() {
    let t4 = this.o;
    const s4 = this.t;
    if (e && void 0 === t4) {
      const e5 = void 0 !== s4 && 1 === s4.length;
      e5 && (t4 = o.get(s4)), void 0 === t4 && ((this.o = t4 = new CSSStyleSheet()).replaceSync(this.cssText), e5 && o.set(s4, t4));
    }
    return t4;
  }
  toString() {
    return this.cssText;
  }
};
var r = (t4) => new n("string" == typeof t4 ? t4 : t4 + "", void 0, s);
var i = (t4, ...e5) => {
  const o6 = 1 === t4.length ? t4[0] : e5.reduce((e6, s4, o7) => e6 + ((t5) => {
    if (true === t5._$cssResult$) return t5.cssText;
    if ("number" == typeof t5) return t5;
    throw Error("Value passed to 'css' function must be a 'css' function result: " + t5 + ". Use 'unsafeCSS' to pass non-literal values, but take care to ensure page security.");
  })(s4) + t4[o7 + 1], t4[0]);
  return new n(o6, t4, s);
};
var S = (s4, o6) => {
  if (e) s4.adoptedStyleSheets = o6.map((t4) => t4 instanceof CSSStyleSheet ? t4 : t4.styleSheet);
  else for (const e5 of o6) {
    const o7 = document.createElement("style"), n5 = t.litNonce;
    void 0 !== n5 && o7.setAttribute("nonce", n5), o7.textContent = e5.cssText, s4.appendChild(o7);
  }
};
var c = e ? (t4) => t4 : (t4) => t4 instanceof CSSStyleSheet ? ((t5) => {
  let e5 = "";
  for (const s4 of t5.cssRules) e5 += s4.cssText;
  return r(e5);
})(t4) : t4;

// node_modules/@lit/reactive-element/reactive-element.js
var { is: i2, defineProperty: e2, getOwnPropertyDescriptor: h, getOwnPropertyNames: r2, getOwnPropertySymbols: o2, getPrototypeOf: n2 } = Object;
var a = globalThis;
var c2 = a.trustedTypes;
var l = c2 ? c2.emptyScript : "";
var p = a.reactiveElementPolyfillSupport;
var d = (t4, s4) => t4;
var u = { toAttribute(t4, s4) {
  switch (s4) {
    case Boolean:
      t4 = t4 ? l : null;
      break;
    case Object:
    case Array:
      t4 = null == t4 ? t4 : JSON.stringify(t4);
  }
  return t4;
}, fromAttribute(t4, s4) {
  let i5 = t4;
  switch (s4) {
    case Boolean:
      i5 = null !== t4;
      break;
    case Number:
      i5 = null === t4 ? null : Number(t4);
      break;
    case Object:
    case Array:
      try {
        i5 = JSON.parse(t4);
      } catch (t5) {
        i5 = null;
      }
  }
  return i5;
} };
var f = (t4, s4) => !i2(t4, s4);
var b = { attribute: true, type: String, converter: u, reflect: false, useDefault: false, hasChanged: f };
Symbol.metadata ?? (Symbol.metadata = Symbol("metadata")), a.litPropertyMetadata ?? (a.litPropertyMetadata = /* @__PURE__ */ new WeakMap());
var y = class extends HTMLElement {
  static addInitializer(t4) {
    this._$Ei(), (this.l ?? (this.l = [])).push(t4);
  }
  static get observedAttributes() {
    return this.finalize(), this._$Eh && [...this._$Eh.keys()];
  }
  static createProperty(t4, s4 = b) {
    if (s4.state && (s4.attribute = false), this._$Ei(), this.prototype.hasOwnProperty(t4) && ((s4 = Object.create(s4)).wrapped = true), this.elementProperties.set(t4, s4), !s4.noAccessor) {
      const i5 = Symbol(), h3 = this.getPropertyDescriptor(t4, i5, s4);
      void 0 !== h3 && e2(this.prototype, t4, h3);
    }
  }
  static getPropertyDescriptor(t4, s4, i5) {
    const { get: e5, set: r6 } = h(this.prototype, t4) ?? { get() {
      return this[s4];
    }, set(t5) {
      this[s4] = t5;
    } };
    return { get: e5, set(s5) {
      const h3 = e5?.call(this);
      r6?.call(this, s5), this.requestUpdate(t4, h3, i5);
    }, configurable: true, enumerable: true };
  }
  static getPropertyOptions(t4) {
    return this.elementProperties.get(t4) ?? b;
  }
  static _$Ei() {
    if (this.hasOwnProperty(d("elementProperties"))) return;
    const t4 = n2(this);
    t4.finalize(), void 0 !== t4.l && (this.l = [...t4.l]), this.elementProperties = new Map(t4.elementProperties);
  }
  static finalize() {
    if (this.hasOwnProperty(d("finalized"))) return;
    if (this.finalized = true, this._$Ei(), this.hasOwnProperty(d("properties"))) {
      const t5 = this.properties, s4 = [...r2(t5), ...o2(t5)];
      for (const i5 of s4) this.createProperty(i5, t5[i5]);
    }
    const t4 = this[Symbol.metadata];
    if (null !== t4) {
      const s4 = litPropertyMetadata.get(t4);
      if (void 0 !== s4) for (const [t5, i5] of s4) this.elementProperties.set(t5, i5);
    }
    this._$Eh = /* @__PURE__ */ new Map();
    for (const [t5, s4] of this.elementProperties) {
      const i5 = this._$Eu(t5, s4);
      void 0 !== i5 && this._$Eh.set(i5, t5);
    }
    this.elementStyles = this.finalizeStyles(this.styles);
  }
  static finalizeStyles(s4) {
    const i5 = [];
    if (Array.isArray(s4)) {
      const e5 = new Set(s4.flat(1 / 0).reverse());
      for (const s5 of e5) i5.unshift(c(s5));
    } else void 0 !== s4 && i5.push(c(s4));
    return i5;
  }
  static _$Eu(t4, s4) {
    const i5 = s4.attribute;
    return false === i5 ? void 0 : "string" == typeof i5 ? i5 : "string" == typeof t4 ? t4.toLowerCase() : void 0;
  }
  constructor() {
    super(), this._$Ep = void 0, this.isUpdatePending = false, this.hasUpdated = false, this._$Em = null, this._$Ev();
  }
  _$Ev() {
    this._$ES = new Promise((t4) => this.enableUpdating = t4), this._$AL = /* @__PURE__ */ new Map(), this._$E_(), this.requestUpdate(), this.constructor.l?.forEach((t4) => t4(this));
  }
  addController(t4) {
    (this._$EO ?? (this._$EO = /* @__PURE__ */ new Set())).add(t4), void 0 !== this.renderRoot && this.isConnected && t4.hostConnected?.();
  }
  removeController(t4) {
    this._$EO?.delete(t4);
  }
  _$E_() {
    const t4 = /* @__PURE__ */ new Map(), s4 = this.constructor.elementProperties;
    for (const i5 of s4.keys()) this.hasOwnProperty(i5) && (t4.set(i5, this[i5]), delete this[i5]);
    t4.size > 0 && (this._$Ep = t4);
  }
  createRenderRoot() {
    const t4 = this.shadowRoot ?? this.attachShadow(this.constructor.shadowRootOptions);
    return S(t4, this.constructor.elementStyles), t4;
  }
  connectedCallback() {
    this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this.enableUpdating(true), this._$EO?.forEach((t4) => t4.hostConnected?.());
  }
  enableUpdating(t4) {
  }
  disconnectedCallback() {
    this._$EO?.forEach((t4) => t4.hostDisconnected?.());
  }
  attributeChangedCallback(t4, s4, i5) {
    this._$AK(t4, i5);
  }
  _$ET(t4, s4) {
    const i5 = this.constructor.elementProperties.get(t4), e5 = this.constructor._$Eu(t4, i5);
    if (void 0 !== e5 && true === i5.reflect) {
      const h3 = (void 0 !== i5.converter?.toAttribute ? i5.converter : u).toAttribute(s4, i5.type);
      this._$Em = t4, null == h3 ? this.removeAttribute(e5) : this.setAttribute(e5, h3), this._$Em = null;
    }
  }
  _$AK(t4, s4) {
    const i5 = this.constructor, e5 = i5._$Eh.get(t4);
    if (void 0 !== e5 && this._$Em !== e5) {
      const t5 = i5.getPropertyOptions(e5), h3 = "function" == typeof t5.converter ? { fromAttribute: t5.converter } : void 0 !== t5.converter?.fromAttribute ? t5.converter : u;
      this._$Em = e5;
      const r6 = h3.fromAttribute(s4, t5.type);
      this[e5] = r6 ?? this._$Ej?.get(e5) ?? r6, this._$Em = null;
    }
  }
  requestUpdate(t4, s4, i5, e5 = false, h3) {
    if (void 0 !== t4) {
      const r6 = this.constructor;
      if (false === e5 && (h3 = this[t4]), i5 ?? (i5 = r6.getPropertyOptions(t4)), !((i5.hasChanged ?? f)(h3, s4) || i5.useDefault && i5.reflect && h3 === this._$Ej?.get(t4) && !this.hasAttribute(r6._$Eu(t4, i5)))) return;
      this.C(t4, s4, i5);
    }
    false === this.isUpdatePending && (this._$ES = this._$EP());
  }
  C(t4, s4, { useDefault: i5, reflect: e5, wrapped: h3 }, r6) {
    i5 && !(this._$Ej ?? (this._$Ej = /* @__PURE__ */ new Map())).has(t4) && (this._$Ej.set(t4, r6 ?? s4 ?? this[t4]), true !== h3 || void 0 !== r6) || (this._$AL.has(t4) || (this.hasUpdated || i5 || (s4 = void 0), this._$AL.set(t4, s4)), true === e5 && this._$Em !== t4 && (this._$Eq ?? (this._$Eq = /* @__PURE__ */ new Set())).add(t4));
  }
  async _$EP() {
    this.isUpdatePending = true;
    try {
      await this._$ES;
    } catch (t5) {
      Promise.reject(t5);
    }
    const t4 = this.scheduleUpdate();
    return null != t4 && await t4, !this.isUpdatePending;
  }
  scheduleUpdate() {
    return this.performUpdate();
  }
  performUpdate() {
    if (!this.isUpdatePending) return;
    if (!this.hasUpdated) {
      if (this.renderRoot ?? (this.renderRoot = this.createRenderRoot()), this._$Ep) {
        for (const [t6, s5] of this._$Ep) this[t6] = s5;
        this._$Ep = void 0;
      }
      const t5 = this.constructor.elementProperties;
      if (t5.size > 0) for (const [s5, i5] of t5) {
        const { wrapped: t6 } = i5, e5 = this[s5];
        true !== t6 || this._$AL.has(s5) || void 0 === e5 || this.C(s5, void 0, i5, e5);
      }
    }
    let t4 = false;
    const s4 = this._$AL;
    try {
      t4 = this.shouldUpdate(s4), t4 ? (this.willUpdate(s4), this._$EO?.forEach((t5) => t5.hostUpdate?.()), this.update(s4)) : this._$EM();
    } catch (s5) {
      throw t4 = false, this._$EM(), s5;
    }
    t4 && this._$AE(s4);
  }
  willUpdate(t4) {
  }
  _$AE(t4) {
    this._$EO?.forEach((t5) => t5.hostUpdated?.()), this.hasUpdated || (this.hasUpdated = true, this.firstUpdated(t4)), this.updated(t4);
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
  shouldUpdate(t4) {
    return true;
  }
  update(t4) {
    this._$Eq && (this._$Eq = this._$Eq.forEach((t5) => this._$ET(t5, this[t5]))), this._$EM();
  }
  updated(t4) {
  }
  firstUpdated(t4) {
  }
};
y.elementStyles = [], y.shadowRootOptions = { mode: "open" }, y[d("elementProperties")] = /* @__PURE__ */ new Map(), y[d("finalized")] = /* @__PURE__ */ new Map(), p?.({ ReactiveElement: y }), (a.reactiveElementVersions ?? (a.reactiveElementVersions = [])).push("2.1.2");

// node_modules/lit-html/lit-html.js
var t2 = globalThis;
var i3 = (t4) => t4;
var s2 = t2.trustedTypes;
var e3 = s2 ? s2.createPolicy("lit-html", { createHTML: (t4) => t4 }) : void 0;
var h2 = "$lit$";
var o3 = `lit$${Math.random().toFixed(9).slice(2)}$`;
var n3 = "?" + o3;
var r3 = `<${n3}>`;
var l2 = document;
var c3 = () => l2.createComment("");
var a2 = (t4) => null === t4 || "object" != typeof t4 && "function" != typeof t4;
var u2 = Array.isArray;
var d2 = (t4) => u2(t4) || "function" == typeof t4?.[Symbol.iterator];
var f2 = "[ 	\n\f\r]";
var v = /<(?:(!--|\/[^a-zA-Z])|(\/?[a-zA-Z][^>\s]*)|(\/?$))/g;
var _ = /-->/g;
var m = />/g;
var p2 = RegExp(`>|${f2}(?:([^\\s"'>=/]+)(${f2}*=${f2}*(?:[^ 	
\f\r"'\`<>=]|("|')|))|$)`, "g");
var g = /'/g;
var $ = /"/g;
var y2 = /^(?:script|style|textarea|title)$/i;
var x = (t4) => (i5, ...s4) => ({ _$litType$: t4, strings: i5, values: s4 });
var b2 = x(1);
var w = x(2);
var T = x(3);
var E = Symbol.for("lit-noChange");
var A = Symbol.for("lit-nothing");
var C = /* @__PURE__ */ new WeakMap();
var P = l2.createTreeWalker(l2, 129);
function V(t4, i5) {
  if (!u2(t4) || !t4.hasOwnProperty("raw")) throw Error("invalid template strings array");
  return void 0 !== e3 ? e3.createHTML(i5) : i5;
}
var N = (t4, i5) => {
  const s4 = t4.length - 1, e5 = [];
  let n5, l3 = 2 === i5 ? "<svg>" : 3 === i5 ? "<math>" : "", c4 = v;
  for (let i6 = 0; i6 < s4; i6++) {
    const s5 = t4[i6];
    let a3, u3, d3 = -1, f3 = 0;
    for (; f3 < s5.length && (c4.lastIndex = f3, u3 = c4.exec(s5), null !== u3); ) f3 = c4.lastIndex, c4 === v ? "!--" === u3[1] ? c4 = _ : void 0 !== u3[1] ? c4 = m : void 0 !== u3[2] ? (y2.test(u3[2]) && (n5 = RegExp("</" + u3[2], "g")), c4 = p2) : void 0 !== u3[3] && (c4 = p2) : c4 === p2 ? ">" === u3[0] ? (c4 = n5 ?? v, d3 = -1) : void 0 === u3[1] ? d3 = -2 : (d3 = c4.lastIndex - u3[2].length, a3 = u3[1], c4 = void 0 === u3[3] ? p2 : '"' === u3[3] ? $ : g) : c4 === $ || c4 === g ? c4 = p2 : c4 === _ || c4 === m ? c4 = v : (c4 = p2, n5 = void 0);
    const x2 = c4 === p2 && t4[i6 + 1].startsWith("/>") ? " " : "";
    l3 += c4 === v ? s5 + r3 : d3 >= 0 ? (e5.push(a3), s5.slice(0, d3) + h2 + s5.slice(d3) + o3 + x2) : s5 + o3 + (-2 === d3 ? i6 : x2);
  }
  return [V(t4, l3 + (t4[s4] || "<?>") + (2 === i5 ? "</svg>" : 3 === i5 ? "</math>" : "")), e5];
};
var S2 = class _S {
  constructor({ strings: t4, _$litType$: i5 }, e5) {
    let r6;
    this.parts = [];
    let l3 = 0, a3 = 0;
    const u3 = t4.length - 1, d3 = this.parts, [f3, v2] = N(t4, i5);
    if (this.el = _S.createElement(f3, e5), P.currentNode = this.el.content, 2 === i5 || 3 === i5) {
      const t5 = this.el.content.firstChild;
      t5.replaceWith(...t5.childNodes);
    }
    for (; null !== (r6 = P.nextNode()) && d3.length < u3; ) {
      if (1 === r6.nodeType) {
        if (r6.hasAttributes()) for (const t5 of r6.getAttributeNames()) if (t5.endsWith(h2)) {
          const i6 = v2[a3++], s4 = r6.getAttribute(t5).split(o3), e6 = /([.?@])?(.*)/.exec(i6);
          d3.push({ type: 1, index: l3, name: e6[2], strings: s4, ctor: "." === e6[1] ? I : "?" === e6[1] ? L : "@" === e6[1] ? z : H }), r6.removeAttribute(t5);
        } else t5.startsWith(o3) && (d3.push({ type: 6, index: l3 }), r6.removeAttribute(t5));
        if (y2.test(r6.tagName)) {
          const t5 = r6.textContent.split(o3), i6 = t5.length - 1;
          if (i6 > 0) {
            r6.textContent = s2 ? s2.emptyScript : "";
            for (let s4 = 0; s4 < i6; s4++) r6.append(t5[s4], c3()), P.nextNode(), d3.push({ type: 2, index: ++l3 });
            r6.append(t5[i6], c3());
          }
        }
      } else if (8 === r6.nodeType) if (r6.data === n3) d3.push({ type: 2, index: l3 });
      else {
        let t5 = -1;
        for (; -1 !== (t5 = r6.data.indexOf(o3, t5 + 1)); ) d3.push({ type: 7, index: l3 }), t5 += o3.length - 1;
      }
      l3++;
    }
  }
  static createElement(t4, i5) {
    const s4 = l2.createElement("template");
    return s4.innerHTML = t4, s4;
  }
};
function M(t4, i5, s4 = t4, e5) {
  if (i5 === E) return i5;
  let h3 = void 0 !== e5 ? s4._$Co?.[e5] : s4._$Cl;
  const o6 = a2(i5) ? void 0 : i5._$litDirective$;
  return h3?.constructor !== o6 && (h3?._$AO?.(false), void 0 === o6 ? h3 = void 0 : (h3 = new o6(t4), h3._$AT(t4, s4, e5)), void 0 !== e5 ? (s4._$Co ?? (s4._$Co = []))[e5] = h3 : s4._$Cl = h3), void 0 !== h3 && (i5 = M(t4, h3._$AS(t4, i5.values), h3, e5)), i5;
}
var R = class {
  constructor(t4, i5) {
    this._$AV = [], this._$AN = void 0, this._$AD = t4, this._$AM = i5;
  }
  get parentNode() {
    return this._$AM.parentNode;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  u(t4) {
    const { el: { content: i5 }, parts: s4 } = this._$AD, e5 = (t4?.creationScope ?? l2).importNode(i5, true);
    P.currentNode = e5;
    let h3 = P.nextNode(), o6 = 0, n5 = 0, r6 = s4[0];
    for (; void 0 !== r6; ) {
      if (o6 === r6.index) {
        let i6;
        2 === r6.type ? i6 = new k(h3, h3.nextSibling, this, t4) : 1 === r6.type ? i6 = new r6.ctor(h3, r6.name, r6.strings, this, t4) : 6 === r6.type && (i6 = new Z(h3, this, t4)), this._$AV.push(i6), r6 = s4[++n5];
      }
      o6 !== r6?.index && (h3 = P.nextNode(), o6++);
    }
    return P.currentNode = l2, e5;
  }
  p(t4) {
    let i5 = 0;
    for (const s4 of this._$AV) void 0 !== s4 && (void 0 !== s4.strings ? (s4._$AI(t4, s4, i5), i5 += s4.strings.length - 2) : s4._$AI(t4[i5])), i5++;
  }
};
var k = class _k {
  get _$AU() {
    return this._$AM?._$AU ?? this._$Cv;
  }
  constructor(t4, i5, s4, e5) {
    this.type = 2, this._$AH = A, this._$AN = void 0, this._$AA = t4, this._$AB = i5, this._$AM = s4, this.options = e5, this._$Cv = e5?.isConnected ?? true;
  }
  get parentNode() {
    let t4 = this._$AA.parentNode;
    const i5 = this._$AM;
    return void 0 !== i5 && 11 === t4?.nodeType && (t4 = i5.parentNode), t4;
  }
  get startNode() {
    return this._$AA;
  }
  get endNode() {
    return this._$AB;
  }
  _$AI(t4, i5 = this) {
    t4 = M(this, t4, i5), a2(t4) ? t4 === A || null == t4 || "" === t4 ? (this._$AH !== A && this._$AR(), this._$AH = A) : t4 !== this._$AH && t4 !== E && this._(t4) : void 0 !== t4._$litType$ ? this.$(t4) : void 0 !== t4.nodeType ? this.T(t4) : d2(t4) ? this.k(t4) : this._(t4);
  }
  O(t4) {
    return this._$AA.parentNode.insertBefore(t4, this._$AB);
  }
  T(t4) {
    this._$AH !== t4 && (this._$AR(), this._$AH = this.O(t4));
  }
  _(t4) {
    this._$AH !== A && a2(this._$AH) ? this._$AA.nextSibling.data = t4 : this.T(l2.createTextNode(t4)), this._$AH = t4;
  }
  $(t4) {
    const { values: i5, _$litType$: s4 } = t4, e5 = "number" == typeof s4 ? this._$AC(t4) : (void 0 === s4.el && (s4.el = S2.createElement(V(s4.h, s4.h[0]), this.options)), s4);
    if (this._$AH?._$AD === e5) this._$AH.p(i5);
    else {
      const t5 = new R(e5, this), s5 = t5.u(this.options);
      t5.p(i5), this.T(s5), this._$AH = t5;
    }
  }
  _$AC(t4) {
    let i5 = C.get(t4.strings);
    return void 0 === i5 && C.set(t4.strings, i5 = new S2(t4)), i5;
  }
  k(t4) {
    u2(this._$AH) || (this._$AH = [], this._$AR());
    const i5 = this._$AH;
    let s4, e5 = 0;
    for (const h3 of t4) e5 === i5.length ? i5.push(s4 = new _k(this.O(c3()), this.O(c3()), this, this.options)) : s4 = i5[e5], s4._$AI(h3), e5++;
    e5 < i5.length && (this._$AR(s4 && s4._$AB.nextSibling, e5), i5.length = e5);
  }
  _$AR(t4 = this._$AA.nextSibling, s4) {
    for (this._$AP?.(false, true, s4); t4 !== this._$AB; ) {
      const s5 = i3(t4).nextSibling;
      i3(t4).remove(), t4 = s5;
    }
  }
  setConnected(t4) {
    void 0 === this._$AM && (this._$Cv = t4, this._$AP?.(t4));
  }
};
var H = class {
  get tagName() {
    return this.element.tagName;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  constructor(t4, i5, s4, e5, h3) {
    this.type = 1, this._$AH = A, this._$AN = void 0, this.element = t4, this.name = i5, this._$AM = e5, this.options = h3, s4.length > 2 || "" !== s4[0] || "" !== s4[1] ? (this._$AH = Array(s4.length - 1).fill(new String()), this.strings = s4) : this._$AH = A;
  }
  _$AI(t4, i5 = this, s4, e5) {
    const h3 = this.strings;
    let o6 = false;
    if (void 0 === h3) t4 = M(this, t4, i5, 0), o6 = !a2(t4) || t4 !== this._$AH && t4 !== E, o6 && (this._$AH = t4);
    else {
      const e6 = t4;
      let n5, r6;
      for (t4 = h3[0], n5 = 0; n5 < h3.length - 1; n5++) r6 = M(this, e6[s4 + n5], i5, n5), r6 === E && (r6 = this._$AH[n5]), o6 || (o6 = !a2(r6) || r6 !== this._$AH[n5]), r6 === A ? t4 = A : t4 !== A && (t4 += (r6 ?? "") + h3[n5 + 1]), this._$AH[n5] = r6;
    }
    o6 && !e5 && this.j(t4);
  }
  j(t4) {
    t4 === A ? this.element.removeAttribute(this.name) : this.element.setAttribute(this.name, t4 ?? "");
  }
};
var I = class extends H {
  constructor() {
    super(...arguments), this.type = 3;
  }
  j(t4) {
    this.element[this.name] = t4 === A ? void 0 : t4;
  }
};
var L = class extends H {
  constructor() {
    super(...arguments), this.type = 4;
  }
  j(t4) {
    this.element.toggleAttribute(this.name, !!t4 && t4 !== A);
  }
};
var z = class extends H {
  constructor(t4, i5, s4, e5, h3) {
    super(t4, i5, s4, e5, h3), this.type = 5;
  }
  _$AI(t4, i5 = this) {
    if ((t4 = M(this, t4, i5, 0) ?? A) === E) return;
    const s4 = this._$AH, e5 = t4 === A && s4 !== A || t4.capture !== s4.capture || t4.once !== s4.once || t4.passive !== s4.passive, h3 = t4 !== A && (s4 === A || e5);
    e5 && this.element.removeEventListener(this.name, this, s4), h3 && this.element.addEventListener(this.name, this, t4), this._$AH = t4;
  }
  handleEvent(t4) {
    "function" == typeof this._$AH ? this._$AH.call(this.options?.host ?? this.element, t4) : this._$AH.handleEvent(t4);
  }
};
var Z = class {
  constructor(t4, i5, s4) {
    this.element = t4, this.type = 6, this._$AN = void 0, this._$AM = i5, this.options = s4;
  }
  get _$AU() {
    return this._$AM._$AU;
  }
  _$AI(t4) {
    M(this, t4);
  }
};
var B = t2.litHtmlPolyfillSupport;
B?.(S2, k), (t2.litHtmlVersions ?? (t2.litHtmlVersions = [])).push("3.3.2");
var D = (t4, i5, s4) => {
  const e5 = s4?.renderBefore ?? i5;
  let h3 = e5._$litPart$;
  if (void 0 === h3) {
    const t5 = s4?.renderBefore ?? null;
    e5._$litPart$ = h3 = new k(i5.insertBefore(c3(), t5), t5, void 0, s4 ?? {});
  }
  return h3._$AI(t4), h3;
};

// node_modules/lit-element/lit-element.js
var s3 = globalThis;
var i4 = class extends y {
  constructor() {
    super(...arguments), this.renderOptions = { host: this }, this._$Do = void 0;
  }
  createRenderRoot() {
    var _a;
    const t4 = super.createRenderRoot();
    return (_a = this.renderOptions).renderBefore ?? (_a.renderBefore = t4.firstChild), t4;
  }
  update(t4) {
    const r6 = this.render();
    this.hasUpdated || (this.renderOptions.isConnected = this.isConnected), super.update(t4), this._$Do = D(r6, this.renderRoot, this.renderOptions);
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

// node_modules/@lit/reactive-element/decorators/custom-element.js
var t3 = (t4) => (e5, o6) => {
  const defineSafely = () => {
    if (!customElements.get(t4)) {
      customElements.define(t4, e5);
    }
  };
  void 0 !== o6 ? o6.addInitializer(() => {
    defineSafely();
  }) : defineSafely();
};

// node_modules/@lit/reactive-element/decorators/property.js
var o5 = { attribute: true, type: String, converter: u, reflect: false, hasChanged: f };
var r4 = (t4 = o5, e5, r6) => {
  const { kind: n5, metadata: i5 } = r6;
  let s4 = globalThis.litPropertyMetadata.get(i5);
  if (void 0 === s4 && globalThis.litPropertyMetadata.set(i5, s4 = /* @__PURE__ */ new Map()), "setter" === n5 && ((t4 = Object.create(t4)).wrapped = true), s4.set(r6.name, t4), "accessor" === n5) {
    const { name: o6 } = r6;
    return { set(r7) {
      const n6 = e5.get.call(this);
      e5.set.call(this, r7), this.requestUpdate(o6, n6, t4, true, r7);
    }, init(e6) {
      return void 0 !== e6 && this.C(o6, void 0, t4, e6), e6;
    } };
  }
  if ("setter" === n5) {
    const { name: o6 } = r6;
    return function(r7) {
      const n6 = this[o6];
      e5.call(this, r7), this.requestUpdate(o6, n6, t4, true, r7);
    };
  }
  throw Error("Unsupported decorator location: " + n5);
};
function n4(t4) {
  return (e5, o6) => "object" == typeof o6 ? r4(t4, e5, o6) : ((t5, e6, o7) => {
    const r6 = e6.hasOwnProperty(o7);
    return e6.constructor.createProperty(o7, t5), r6 ? Object.getOwnPropertyDescriptor(e6, o7) : void 0;
  })(t4, e5, o6);
}

// node_modules/@lit/reactive-element/decorators/state.js
function r5(r6) {
  return n4({ ...r6, state: true, attribute: false });
}

// frontend/herald-card.ts
window.customCards = window.customCards || [];
[
  {
    type: "herald-card",
    name: "Herald Card",
    description: "Полная карточка Herald",
    preview: true
  },
  {
    type: "ha-herald-general",
    name: "Herald: Общее",
    description: "Краткий статус и сводка Herald",
    preview: true
  },
  {
    type: "ha-herald-policies",
    name: "Herald: Политики",
    description: "Политики уведомлений Herald",
    preview: true
  },
  {
    type: "ha-herald-policy-guide",
    name: "Herald: Памятка",
    description: "Краткая памятка по policy-объектам Herald",
    preview: true
  },
  {
    type: "ha-herald-flows",
    name: "Herald: Потоки",
    description: "Потоки и заглушение Herald",
    preview: true
  },
  {
    type: "ha-herald-languages",
    name: "Herald: Языки",
    description: "Языки пользователей Herald",
    preview: true
  },
  {
    type: "ha-herald-characters",
    name: "Herald: Персонажи",
    description: "Персонажи пользователей Herald",
    preview: true
  },
  {
    type: "ha-herald-mute",
    name: "Herald: Тишина",
    description: "Точечное заглушение Herald",
    preview: true
  },
  {
    type: "ha-herald-rooms",
    name: "Herald: Комнаты",
    description: "Комнаты и fallback-переключатели Herald",
    preview: true
  },
  {
    type: "ha-herald-queue",
    name: "Herald: Очередь",
    description: "Очередь событий Herald",
    preview: true
  },
  {
    type: "ha-herald-feed",
    name: "Herald: Лента",
    description: "Лента доставки Herald",
    preview: true
  },
  {
    type: "ha-herald-recent",
    name: "Herald: Последние",
    description: "Последние уведомления Herald",
    preview: true
  },
  {
    type: "ha-herald-controls",
    name: "Herald: Управление",
    description: "Составная карточка управления Herald",
    preview: true
  },
  {
    type: "ha-herald-overview",
    name: "Herald: Обзор",
    description: "Составная обзорная карточка Herald",
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
  }
  setConfig(config) {
    this._config = {
      ...config,
      view_mode: config.view_mode || this.constructor.viewMode || "full",
      status_entity: config.status_entity || DEFAULT_STATUS_ENTITY,
      today_entity: config.today_entity || DEFAULT_TODAY_ENTITY,
      last_entity: config.last_entity || DEFAULT_LAST_ENTITY,
      queue_entity: config.queue_entity || DEFAULT_QUEUE_ENTITY
    };
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
      ...(this._config.language_entities ?? []),
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
              <h2>${this._config.title ?? "Центр уведомлений Herald"}</h2>
              <p class="subhead">Нативная карточка управления уведомлениями: статус, очередь, пользователи, комнаты и последние события.</p>
            </div>
            <div class="stats">
              ${this._renderStat("\u0421\u0435\u0433\u043E\u0434\u043D\u044F", today.state)}
              ${this._renderStat("\u041E\u0447\u0435\u0440\u0435\u0434\u044C", queue.state)}
              ${this._renderStat("\u041F\u043E\u0441\u043B\u0435\u0434\u043D\u0435\u0435", last.state)}
            </div>
          </div>
        </div>
      </ha-card>
    `;
    const policySection = notificationRegistry.length ? this._renderPanelCard(
      "Политики уведомлений",
      "Умная панель правил уведомлений, собранная из live config",
      b2`
        <div class="stats compact">
          ${this._renderStat("Всего", notificationSummary.count ?? notificationRegistry.length)}
          ${this._renderStat("Включено", notificationSummary.enabled_count ?? "нет")}
          ${this._renderStat("Выключено", notificationSummary.disabled_count ?? "нет")}
          ${this._renderStat("Кастом", notificationSummary.customized_count ?? "нет")}
          ${this._renderStat("Фильтр", filteredRegistry.length)}
          ${this._renderStat("Страница", policyPage.totalPages ? `${policyPage.page}/${policyPage.totalPages}` : "0/0")}
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
      "Памятка по policy",
      "Один policy-объект на одно уведомление: включение, режим, каналы и overrides",
      b2`
        <div class="notification">
          <p>Используй отключение, если нужно полностью выключить конкретное уведомление. Для выбора типа доставки используй режим доставки. Если нужен точный набор каналов, переведи policy в кастом и сохрани каналы. Переопределение уровня и cooldown нужны только для редких точечных исключений.</p>
        </div>
      `,
      A,
      "policy-guide-panel"
    ) : A;
    const flowsSection = this._renderPanelCard(
      "Потоки",
      "Временное включение и заглушение потоков",
      b2`
        <div class="flow-grid">
          ${Object.entries(flowStates).map(([flow, enabled]) => this._renderFlow(flow, enabled, snoozedFlows[flow]))}
        </div>
      `,
      A,
      "flows-panel"
    );
    const languagesSection = languageEntities.length ? this._renderPanelCard(
      "Языки",
      "Язык уведомлений по пользователям",
      b2`
        <div class="language-grid">
          ${languageEntities.map((entityId) => this._renderLanguage(entityId))}
        </div>
      `,
      A,
      "languages-panel"
    ) : renderEmptySection("Языки", "Язык уведомлений по пользователям", "Пользовательские языковые контролы пока не найдены.", "languages-panel");
    const charactersSection = characterEntities.length ? this._renderPanelCard(
      "Персонажи",
      "ИИ-персонаж по пользователям",
      b2`
        <div class="character-grid">
          ${characterEntities.map((entityId) => this._renderCharacter(entityId))}
        </div>
      `,
      A,
      "characters-panel"
    ) : renderEmptySection("Персонажи", "ИИ-персонаж по пользователям", "Пользовательские персонажи пока не найдены.", "characters-panel");
    const muteSection = muteEntities.length ? this._renderPanelCard(
      "Заглушение",
      "Точечное отключение звука по пользователям",
      b2`
        <div class="mute-grid">
          ${muteEntities.map((entityId) => this._renderMute(entityId))}
        </div>
      `,
      A,
      "mute-panel"
    ) : renderEmptySection("Заглушение", "Точечное отключение звука по пользователям", "Персональные переключатели тишины пока не найдены.", "mute-panel");
    const roomsSection = roomEntities.length ? this._renderPanelCard(
      "Комнаты",
      "Комнаты, присутствие и fallback-переключатели Herald",
      b2`
        <div class="room-grid">
          ${roomEntities.map((item) => this._renderRoom(item))}
        </div>
      `,
      A,
      "rooms-panel"
    ) : renderEmptySection("Комнаты", "Комнаты, присутствие и fallback-переключатели Herald", "Комнатные контролы пока не настроены.", "rooms-panel");
    const queueSection = this._renderPanelCard(
      "Очередь",
      "События, которые ждут отправки или сводки",
      b2`
        <div class="list">
          ${queuedNotifications.length ? queuedNotifications.slice(0, 8).map((item) => this._renderQueuedItem(item)) : b2`<div class="empty">Очередь сейчас пуста.</div>`}
        </div>
      `,
      A,
      "queue-panel"
    );
    const dashboardFeedSection = this._renderPanelCard(
      "Лента панели",
      "Уведомления, доставленные в канал Herald dashboard",
      b2`
        <div class="list">
          ${dashboardFeed.length ? dashboardFeed.slice(0, 8).map((item) => this._renderFeedItem(item)) : b2`<div class="empty">Лента панели пока пуста.</div>`}
        </div>
      `,
      A,
      "feed-panel"
    );
    const recentSection = this._renderPanelCard(
      "Последние уведомления",
      "Последние доставки и сводки",
      b2`
        <div class="list">
          ${recent.length ? recent.slice(0, 8).map((item) => this._renderNotification(item)) : b2`<div class="empty">Уведомлений пока нет.</div>`}
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
      <ha-card class="panel ${panelClass}">
        <div class="panel-shell">
          <div class="panel-header">
            <div>
              <h3>${title}</h3>
              <span>${subtitle}</span>
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
        <strong>${value ?? "нет"}</strong>
      </div>
    `;
  }
  _renderFlow(flow, enabled, snoozedUntil) {
    const snoozed = Boolean(snoozedUntil && !enabled);
    return b2`
      <button class="flow ${enabled ? "enabled" : "disabled"}" @click=${() => this._toggleFlow(flow, enabled)}>
        <span class="flow-name">${this._friendlyFlowName(flow)}</span>
        <span class="flow-state">${enabled ? "включено" : snoozed ? `до ${snoozedUntil}` : "выключено"}</span>
      </button>
    `;
  }
  _renderLanguage(entityId) {
    const entity = this.hass?.states[entityId];
    if (!entity) {
      return A;
    }
    const options = entity.attributes.options ?? DEFAULT_LANGUAGES;
    const label = this._friendlyEntityLabel(entityId, entity);
    return b2`
      <label class="language-card">
        <span>${label}</span>
        <select .value=${entity.state} @change=${(event) => this._setLanguage(entityId, event)}>
          ${options.map((option) => b2`<option value=${option}>${this._friendlyLanguageName(option)}</option>`)}
        </select>
      </label>
    `;
  }
  _renderCharacter(entityId) {
    const entity = this.hass?.states[entityId];
    if (!entity) {
      return A;
    }
    const options = entity.attributes.options ?? [];
    const label = this._friendlyEntityLabel(entityId, entity);
    return b2`
      <label class="language-card">
        <span>${label}</span>
        <select .value=${entity.state} @change=${(event) => this._setSelectOption(entityId, event)}>
          ${options.map((option) => b2`<option value=${option}>${this._friendlyCharacterName(option)}</option>`)}
        </select>
      </label>
    `;
  }
  _renderMute(entityId) {
    const entity = this.hass?.states[entityId];
    if (!entity) {
      return A;
    }
    const muted = entity.state === "on";
    const label = this._friendlyEntityLabel(entityId, entity);
    return b2`
      <article class="room-card ${muted ? "disabled" : "enabled"}">
        <div class="room-head">
          <strong>${label}</strong>
          <span class="pill">${muted ? "тихо" : "активно"}</span>
        </div>
        <div class="room-meta">
          <span>${muted ? "Уведомления заглушены" : "Уведомления активны"}</span>
        </div>
        <button class="room-toggle" @click=${() => this._toggleSwitch(entityId, muted)}>
          ${muted ? "Включить звук" : "Заглушить"}
        </button>
      </article>
    `;
  }
  _renderRoom(item) {
    const sensorEntityId = item?.sensor ?? "";
    const fallbackEntityId = item?.fallback ?? "";
    const sensor = this.hass?.states[sensorEntityId];
    const fallback = this.hass?.states[fallbackEntityId];
    if (!sensor && !fallback) {
      return A;
    }
    const roomName = item?.room ?? sensor?.attributes?.room ?? fallback?.attributes?.room ?? sensorEntityId ?? fallbackEntityId;
    const sensorOn = sensor?.state === "on";
    const fallbackOn = fallback?.state === "on";
    const resolvedFrom = sensor?.attributes?.resolved_from ?? "herald_fallback_switch";
    const resolvedFromLabel = this._friendlyResolvedFrom(resolvedFrom);
    return b2`
      <article class="room-card ${sensorOn ? "occupied" : "idle"}">
        <div class="room-head">
          <strong>${this._friendlyRoomLabel(roomName)}</strong>
          <span class="pill">${sensorOn ? "занято" : "свободно"}</span>
        </div>
        <div class="room-meta">
          <span>Сенсор: ${this._friendlyBinaryState(sensor?.state)}</span>
          <span>Fallback: ${this._friendlyBinaryState(fallback?.state)}</span>
          <span>Источник: ${resolvedFromLabel}</span>
        </div>
        ${fallback ? b2`
              <button class="room-toggle" @click=${() => this._toggleSwitch(fallbackEntityId, fallbackOn)}>
                ${fallbackOn ? "Выключить fallback" : "Включить fallback"}
              </button>
            ` : A}
      </article>
    `;
  }
  _renderNotification(item) {
    const channels = this._formatChannels(Array.isArray(item.channels) ? item.channels : []) || "авто";
    return b2`
      <article class="notification">
        <div class="notification-head">
          <strong>${this._friendlyDeliveryItemTitle(item, "Herald")}</strong>
          <span class="pill">${this._friendlyLevelLabel(item.level ?? "info")}</span>
        </div>
        <p>${String(item.message ?? "")}</p>
        <footer>
          <span>${channels}</span>
          <span>${String(item.timestamp ?? "")}</span>
        </footer>
      </article>
    `;
  }
  _renderQueuedItem(item) {
    const channels = Array.isArray(item.channels) && item.channels.length ? item.channels.join(", ") : "авто";
    return b2`
      <article class="notification">
        <div class="notification-head">
          <strong>${this._friendlyDeliveryItemTitle(item, "Уведомление в очереди")}</strong>
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
          <strong>${this._friendlyDeliveryItemTitle(item, "Лента панели")}</strong>
          <span class="pill">${this._friendlyLevelLabel(item.level ?? "info")}</span>
        </div>
        <p>${String(item.message ?? "")}</p>
        <footer>
          <span>${this._friendlyChannelName(channel)}</span>
          <span>${room === "n/a" ? "без комнаты" : this._friendlyRoomLabel(room)}</span>
          <span>${String(item.timestamp ?? "")}</span>
        </footer>
      </article>
    `;
  }
  _renderPolicyTable(pageData, totalItems) {
    return b2`
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
    const key = String(item.notification_key ?? "");
    const effective = item.effective ?? {};
    const policy = item.policy ?? {};
    const lastEventAt = item.last_seen_at ?? item.family_last_event_at ?? "нет";
    const titleLabel = this._friendlyNotificationTitle(item);
    const routeLabel = this._friendlyRouteLabel(item);
    const eventLabel = this._friendlyEventLabel(item.family_last_event_code ?? "n/a");
    const isCustomized = effective.delivery_mode !== "inherit" || Boolean(policy.level_override) || policy.cooldown_override != null || Boolean(policy.notes);
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
            <span class="policy-status ${effective.enabled ? "enabled" : "disabled"}">${effective.enabled ? "вкл" : "выкл"}</span>
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
            <strong>${this._formatChannels(effective.channels ?? []) || "наследовать"}</strong>
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
              ${expanded ? "Скрыть" : "Редактировать"}
            </button>
            <button class="secondary-action" ?disabled=${this._busyPolicy === key} @click=${() => this._togglePolicyEnabled(item)}>
              ${effective.enabled ? "Выключить" : "Включить"}
            </button>
          </div>
        </td>
      </tr>
      ${expanded ? b2`
            <tr class="policy-editor-row">
              <td colspan="8">
                ${this._renderPolicyEditor(item)}
              </td>
            </tr>
          ` : A}
    `;
  }
  _renderPolicyEditor(item) {
    const key = String(item.notification_key ?? "");
    const effective = item.effective ?? {};
    const policy = item.policy ?? {};
    const mode = this._policyDraftValue(key, "delivery_mode", policy.delivery_mode ?? effective.delivery_mode ?? "inherit");
    const availableChannels = item.available_channels ?? [];
    const draftChannels = this._policyDraftChannels(key, item);
    const levelOverride = this._policyDraftValue(key, "level_override", policy.level_override ?? "");
    const cooldownOverride = this._policyDraftValue(
      key,
      "cooldown_override",
      policy.cooldown_override == null ? "" : String(policy.cooldown_override)
    );
    const notesValue = this._policyDraftValue(key, "notes", policy.notes ?? "");
    const busy = this._busyPolicy === key;
    const titleLabel = this._friendlyNotificationTitle(item);
    const routeLabel = this._friendlyRouteLabel(item);
    const eventLabel = this._friendlyEventLabel(item.family_last_event_code ?? "n/a");
    return b2`
      <article class="policy-card policy-card-editor ${effective.enabled ? "enabled" : "disabled"}">
        <div class="policy-meta">
          <span>Уведомление: ${titleLabel}</span>
          <span>Семейство: ${this._friendlyFamilyLabel(item.family ?? "general")}</span>
        </div>
        <div class="policy-meta">
          <span>Маршрут: ${routeLabel}</span>
          <span>Эффективный режим: ${this._friendlyDeliveryMode(effective.delivery_mode ?? "inherit")}</span>
        </div>
        <div class="policy-meta">
          <span>Последнее событие: ${item.last_seen_at ?? item.family_last_event_at ?? "нет"}</span>
          <span>Последний код: ${eventLabel}</span>
        </div>
        <div class="policy-meta">
          <span>Источники: ${this._friendlySourceCount(item.source_count ?? (item.source_files?.length ?? 0))}</span>
          <span>Эффективные каналы: ${this._formatChannels(effective.channels ?? []) || "наследовать"}</span>
        </div>
        <label class="language-card policy-field">
            <span>Режим доставки</span>
            <select .value=${mode} @change=${(event) => this._setPolicyDraft(key, "delivery_mode", event.target.value)}>
              ${["inherit", "disabled", "text_only", "voice_only", "push_only", "custom"].map((option) => b2`<option value=${option}>${this._friendlyDeliveryMode(option)}</option>`)}
          </select>
        </label>
        <label class="language-card policy-field">
          <span>Каналы</span>
          <div class="policy-channel-summary">
            ${mode === "custom" ? `Выбраны: ${this._formatChannels(draftChannels) || "нет"}` : `Наследуются/эффективные: ${this._formatChannels(effective.channels ?? []) || "наследовать"}`}
          </div>
          ${availableChannels.length ? b2`
                <div class="policy-channel-grid">
                  ${availableChannels.map((channel) => b2`
                        <button
                          type="button"
                          title=${channel}
                          class="policy-channel ${draftChannels.includes(channel) ? "selected" : ""}"
                          ?disabled=${mode !== "custom"}
                          @click=${() => this._togglePolicyDraftChannel(key, channel, item)}
                        >
                          ${this._friendlyChannelName(channel)}
                        </button>
                      `)}
                </div>
              ` : b2`<div class="policy-channel-summary">Доступные каналы не найдены.</div>`}
        </label>
        <div class="policy-grid policy-grid-advanced">
          <label class="language-card policy-field">
            <span>Переопределение уровня</span>
            <select .value=${levelOverride} @change=${(event) => this._setPolicyDraft(key, "level_override", event.target.value)}>
              ${["", "debug", "info", "notice", "warning", "critical", "security", "ai", "system"].map((option) => b2`<option value=${option}>${option ? this._friendlyLevelLabel(option) : "наследовать"}</option>`)}
            </select>
          </label>
          <label class="language-card policy-field">
            <span>Переопределение cooldown</span>
            <input
              .value=${cooldownOverride}
              inputmode="numeric"
              placeholder="секунды"
              @input=${(event) => this._setPolicyDraft(key, "cooldown_override", event.target.value)}
            />
          </label>
        </div>
        <label class="language-card policy-field">
          <span>Заметки</span>
          <input
            .value=${notesValue}
            placeholder="зачем существует это правило"
            @input=${(event) => this._setPolicyDraft(key, "notes", event.target.value)}
          />
        </label>
        <div class="policy-actions">
          <button class="secondary-action" ?disabled=${busy} @click=${() => this._savePolicy(item)}>
            Сохранить
          </button>
          <button class="secondary-action" ?disabled=${busy} @click=${() => this._resetPolicy(item)}>
            Сбросить
          </button>
        </div>
      </article>
    `;
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
    if (!this.hass) {
      return;
    }
    const target = event.target;
    await this.hass.callService("select", "select_option", {
      entity_id: entityId,
      option: target.value
    });
  }
  async _toggleSwitch(entityId, enabled) {
    if (!this.hass || !entityId) {
      return;
    }
    await this.hass.callService("switch", enabled ? "turn_off" : "turn_on", {
      entity_id: entityId
    });
  }
  _policyDraftValue(notificationKey, field, fallback) {
    return this._policyDrafts?.[notificationKey]?.[field] ?? fallback;
  }
  _policyDraftChannels(notificationKey, item) {
    const draftValue = this._policyDrafts?.[notificationKey]?.channels;
    if (Array.isArray(draftValue)) {
      return draftValue;
    }
    if (typeof draftValue === "string") {
      return draftValue.split(",").map((part) => part.trim()).filter((part) => part);
    }
    if (Array.isArray(item.policy?.channels) && item.policy.channels.length) {
      return [...item.policy.channels];
    }
    if (Array.isArray(item.effective?.channels)) {
      return [...item.effective.channels];
    }
    return [];
  }
  _setPolicyDraft(notificationKey, field, value) {
    this._policyDrafts = {
      ...this._policyDrafts,
      [notificationKey]: {
        ...(this._policyDrafts?.[notificationKey] ?? {}),
        [field]: value
      }
    };
  }
  _togglePolicyDraftChannel(notificationKey, channel, item) {
    const current = this._policyDraftChannels(notificationKey, item);
    const next = current.includes(channel) ? current.filter((entry) => entry !== channel) : [...current, channel];
    this._setPolicyDraft(notificationKey, "channels", next);
  }
  _friendlyFlowName(flow) {
    const labels = {
      security_alerts: "Безопасность",
      system_events: "Системные события",
      device_alerts: "Устройства",
      ai_events: "ИИ-события",
      energy_events: "Энергия",
      camera_alerts: "Камеры",
      timer_notifications: "Таймеры"
    };
    return labels[flow] ?? this._humanizeCode(flow);
  }
  _friendlyLevelLabel(level) {
    const labels = {
      debug: "отладка",
      info: "инфо",
      notice: "обычное",
      warning: "важное",
      critical: "критичное",
      security: "безопасность",
      ai: "ИИ",
      system: "система"
    };
    return labels[level] ?? this._humanizeCode(level);
  }
  _friendlyChannelName(channel) {
    const labels = {
      system_log_default: "Системный лог",
      persistent_default: "Постоянные уведомления",
      telegram_default: "Telegram",
      voice_auto: "Голос: авто",
      dashboard_default: "Лента Herald",
      push_default: "Push",
      tv_default: "TV"
    };
    return labels[channel] ?? this._humanizeCode(channel);
  }
  _friendlyChannelFamilyLabel(value) {
    const labels = {
      voice: "Голос",
      push: "Push",
      tv: "TV",
      dashboard: "Панель",
      persistent: "Постоянные",
      system_log: "Системный лог",
      mobile_app: "Мобильные"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _friendlyFamilyLabel(value) {
    const labels = {
      general: "Общее",
      ai: "ИИ",
      ai_foundation: "Базовый ИИ",
      energy: "Энергия",
      energy_policy: "Тарифы и бюджет",
      energy_runtime: "Энергосигналы",
      reports: "Брифинги и отчеты",
      system: "Система",
      security: "Безопасность",
      recovery: "Восстановление",
      recovery_ops: "Восстановление",
      timer: "Таймер",
      guests: "Гости",
      adult_content: "18+",
      environment: "Экология",
      geo: "Гео",
      washer: "Стиралка",
      copilot: "Copilot",
      home_mode: "Режим дома",
      device_ops: "Операции устройств",
      manual_lights: "Ручной свет",
      household_power: "Фоновая нагрузка",
      tts: "Озвучка",
      alarm_clock: "Будильник",
      ev_dispatcher: "EV-диспетчер",
      camera: "Камеры"
    };
    return labels[value] ?? this._humanizeCode(value);
  }
  _friendlyDeliveryMode(value) {
    const labels = {
      inherit: "Наследовать",
      disabled: "Отключить",
      text_only: "Только текст",
      voice_only: "Только голос",
      push_only: "Только push",
      custom: "Кастом"
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
      return `Поток · ${this._friendlyFlowName(flowMatch[1])}`;
    }
    const channelFamilyMatch = objectId.match(/^herald_channel_family_(.+)$/);
    if (channelFamilyMatch) {
      return `Семейство каналов · ${this._friendlyChannelFamilyLabel(channelFamilyMatch[1])}`;
    }
    const match = objectId.match(/^herald_user_(.+)_(language|character|silent)$/);
    if (match) {
      const user = this._friendlyUserSlug(match[1]);
      const suffixLabels = {
        language: "Язык",
        character: "Персонаж",
        silent: "Звук"
      };
      return `${user} · ${suffixLabels[match[2]]}`;
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
      abrikos: "Абрикос",
      aleksandr_meshcheriakov: "Александр",
      victoria_meshchryakovf: "Виктория"
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
      ru: "Русский",
      en: "Английский",
      es: "Испанский",
      fr: "Французский",
      de: "Немецкий",
      ca: "Каталанский"
    };
    return labels[String(value ?? "").trim().toLowerCase()] ?? String(value ?? "");
  }
  _friendlyCharacterName(value) {
    const labels = {
      domovoy: "Домовой",
      hestia: "Hestia",
      plugins: "Плагины",
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
    if (codeTitle && codeTitle !== "Нет события") {
      return codeTitle;
    }
    return rawTitle || String(item?.notification_key ?? "Уведомление");
  }
  _friendlyDeliveryItemTitle(item, fallbackTitle = "Уведомление") {
    const rawTitle = String(item?.title ?? "").trim();
    if (rawTitle && this._containsCyrillic(rawTitle) && !this._looksSystemLabel(rawTitle)) {
      return rawTitle;
    }
    const eventLabel = this._friendlyEventLabel(item?.event ?? rawTitle);
    if (eventLabel && eventLabel !== "Нет события") {
      return eventLabel;
    }
    return rawTitle || fallbackTitle;
  }
  _friendlyRoomLabel(value) {
    const raw = String(value ?? "").trim();
    if (!raw || raw === "n/a") {
      return "без комнаты";
    }
    return this._humanizeCode(raw);
  }
  _friendlyRouteLabel(item) {
    const entityId = String(item?.selected_entity ?? "").trim();
    if (!entityId || entityId === "n/a") {
      return "Нет маршрута";
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
      return familyLabel ? `Маршрут · ${familyLabel}` : `Маршрут · ${this._humanizeCode(objectId.replace(/_alert_selected$/, "").replace(/_selected$/, ""))}`;
    }
    if (objectId.endsWith("_attention_required")) {
      return familyLabel ? `Внимание · ${familyLabel}` : `Внимание · ${this._humanizeCode(objectId.replace(/_attention_required$/, ""))}`;
    }
    return this._humanizeCode(objectId || entityId);
  }
  _friendlyEventLabel(code) {
    if (!code || code === "n/a" || code === "idle" || code === "none") {
      return "Нет события";
    }
    const normalized = String(code ?? "").trim().toLowerCase();
    const exact = {
      washer_started_expensive_tariff: "Стиралка запущена на дорогом тарифе",
      washer_finished: "Стирка завершена",
      wifi_guest_detected: "Обнаружен гостевой Wi-Fi",
      adult_content_enabled: "Режим 18+ включен",
      adult_content_disabled: "Режим 18+ выключен",
      morning_briefing: "Утренний брифинг",
      evening_briefing: "Вечерний брифинг",
      daily_report: "Ежедневный отчет",
      weekly_report: "Недельный отчет",
      geomagnetic_storm: "Геомагнитная буря",
      critical_co2: "Критический CO2",
      ollama_unavailable: "Ollama недоступен",
      power_overload: "Перегрузка мощности",
      grid_quality_problem: "Проблема качества сети",
      grid_quality_recovered: "Качество сети восстановлено",
      jump_expensive: "Скачок нагрузки на дорогом тарифе",
      punta_started: "Начался пиковый тариф",
      valle_started: "Начался ночной тариф",
      report_ready: "Отчет готов",
      report_skipped: "Отчет пропущен",
      timer_status: "Статус таймера",
      timer_finished: "Таймер завершен",
      timer_cancelled: "Таймер отменен"
    };
    if (exact[normalized]) {
      return exact[normalized];
    }
    const tokenLabels = {
      ai: "ИИ",
      co2: "CO2",
      pm10: "PM10",
      pm25: "PM2.5",
      ev: "EV",
      tts: "TTS",
      wifi: "Wi-Fi",
      herald: "Herald",
      washer: "стиралка",
      guest: "гость",
      guests: "гости",
      adult: "18+",
      content: "контент",
      mode: "режим",
      started: "запущено",
      finished: "завершено",
      enabled: "включено",
      disabled: "отключено",
      detected: "обнаружено",
      recommendation: "рекомендация",
      critical: "критический",
      warning: "предупреждение",
      alert: "сигнал",
      reminder: "напоминание",
      report: "отчет",
      power: "мощность",
      overload: "перегрузка",
      grid: "сеть",
      quality: "качество",
      problem: "проблема",
      recovered: "восстановлено",
      expensive: "дорогой",
      tariff: "тариф",
      morning: "утренний",
      evening: "вечерний",
      timer: "таймер",
      status: "статус",
      cancelled: "отменено",
      beach: "пляж",
      walk: "прогулка",
      window: "окна",
      unavailable: "недоступно",
      security: "безопасность",
      camera: "камеры",
      suspicious: "подозрительно",
      silence: "тишина",
      anomaly: "аномалия",
      manual: "ручной",
      lights: "свет",
      home: "дом",
      mode: "режим",
      selected: "выбрано"
    };
    const human = normalized.split("_").map((part) => tokenLabels[part] ?? part).join(" ").replace(/\s+/g, " ").trim();
    if (!human) {
      return "Нет события";
    }
    return human.charAt(0).toUpperCase() + human.slice(1);
  }
  _friendlySourceCount(count) {
    const number = Number(count ?? 0) || 0;
    if (number === 1) {
      return "1 источник";
    }
    if (number >= 2 && number <= 4) {
      return `${number} источника`;
    }
    return `${number} источников`;
  }
  _friendlyBinaryState(value) {
    if (value === "on") return "вкл";
    if (value === "off") return "выкл";
    if (value === "n/a" || value == null || value === "") return "нет";
    return this._humanizeCode(value);
  }
  _friendlyResolvedFrom(value) {
    const labels = {
      herald_fallback_switch: "Fallback-переключатель",
      room_presence_sensor: "Сенсор комнаты",
      room_presence_binary_sensor: "Бинарный сенсор комнаты",
      real_room_sensor: "Реальный сенсор комнаты"
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
    this._policySearch = value;
    this._policyPage = 1;
    this._policyExpanded = "";
  }
  _setPolicyFamily(value) {
    this._policyFamily = value;
    this._policyPage = 1;
    this._policyExpanded = "";
  }
  _setPolicyScope(value) {
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
        ...(item.source_files ?? []),
        ...(item.effective?.channels ?? []),
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
        const customized = effective.delivery_mode !== "inherit" || Boolean(policy.level_override) || policy.cooldown_override != null || Boolean(policy.notes);
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
    this._policyExpanded = this._policyExpanded === notificationKey ? "" : notificationKey;
  }
  _setPolicyPage(page) {
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
  async _togglePolicyEnabled(item) {
    if (!this.hass) {
      return;
    }
    const key = String(item.notification_key ?? "");
    this._busyPolicy = key;
    try {
      await this.hass.callService("herald", "set_notification_policy", {
        notification_key: key,
        enabled: !(item.effective?.enabled ?? true)
      });
    } finally {
      this._busyPolicy = "";
    }
  }
  async _savePolicy(item) {
    if (!this.hass) {
      return;
    }
    const key = String(item.notification_key ?? "");
    const mode = this._policyDraftValue(key, "delivery_mode", item.policy?.delivery_mode ?? item.effective?.delivery_mode ?? "inherit");
    const rawChannels = this._policyDraftValue(key, "channels", this._policyDraftChannels(key, item));
    const channels = Array.isArray(rawChannels) ? rawChannels.filter((part) => part) : String(rawChannels).split(",").map((part) => part.trim()).filter((part) => part);
    const levelOverride = this._policyDraftValue(key, "level_override", item.policy?.level_override ?? "");
    const cooldownOverride = this._policyDraftValue(
      key,
      "cooldown_override",
      item.policy?.cooldown_override == null ? "" : String(item.policy.cooldown_override)
    );
    const notes = this._policyDraftValue(key, "notes", item.policy?.notes ?? "");
    this._busyPolicy = key;
    try {
      const payload = {
        notification_key: key,
        delivery_mode: mode,
        level_override: levelOverride || "",
        cooldown_override: cooldownOverride || "",
        notes: notes || ""
      };
      if (mode === "custom") {
        payload.channels = channels;
      }
      await this.hass.callService("herald", "set_notification_policy", payload);
    } finally {
      this._busyPolicy = "";
    }
  }
  async _resetPolicy(item) {
    if (!this.hass) {
      return;
    }
    const key = String(item.notification_key ?? "");
    this._busyPolicy = key;
    try {
      await this.hass.callService("herald", "reset_notification_policy", {
        notification_key: key
      });
      if (this._policyDrafts?.[key]) {
        const nextDrafts = { ...this._policyDrafts };
        delete nextDrafts[key];
        this._policyDrafts = nextDrafts;
      }
    } finally {
      this._busyPolicy = "";
    }
  }
};
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

    .policy-card-editor {
      border: none;
      padding: 0;
      background: transparent;
    }

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
__decorateClass([
  n4({ attribute: false })
], HeraldCard.prototype, "hass", 2);
__decorateClass([
  r5()
], HeraldCard.prototype, "_config", 2);
__decorateClass([
  r5()
], HeraldCard.prototype, "_busyFlow", 2);
__decorateClass([
  r5()
], HeraldCard.prototype, "_busyPolicy", 2);
__decorateClass([
  r5()
], HeraldCard.prototype, "_policyDrafts", 2);
__decorateClass([
  r5()
], HeraldCard.prototype, "_policySearch", 2);
__decorateClass([
  r5()
], HeraldCard.prototype, "_policyFamily", 2);
__decorateClass([
  r5()
], HeraldCard.prototype, "_policyScope", 2);
__decorateClass([
  r5()
], HeraldCard.prototype, "_policyPage", 2);
__decorateClass([
  r5()
], HeraldCard.prototype, "_policyExpanded", 2);
HeraldCard = __decorateClass([
  t3("herald-card")
], HeraldCard);
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
export {
  HeraldCard
};
