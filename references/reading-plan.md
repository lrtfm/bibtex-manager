# Strang splitting 二阶收敛：精炼阅读计划

## 阅读目标
建立线性无界算子及非线性 PDE 的 Strang splitting 二阶收敛分析框架，并理解与空间离散的一致性问题。

## 阅读顺序
1. Strang (1968)：方法的原始构造与对称组合。
2. Jahnke & Lubich (2000)：无界算子误差界、交换子与正则性假设。
3. Hansen & Ostermann (2009)：半群框架、抽象收敛定理。
4. Besse, Bidégaray & Descombes (2002)：非线性 Schrödinger 方程、流映射与时间误差证明。
5. Descombes & Thalhammer (2010)：局部误差的积分表示。
6. Einkemmer & Ostermann (2015)：非齐次 Dirichlet 条件下的降阶与修正。

## 核心问题
- 如何严格得到非线性 Strang splitting 的局部三阶误差？
- 无界算子的定义域、正则性和稳定性条件分别是什么？
- 空间离散后如何获得关于网格参数 h 一致的时间误差常数？
- 边界条件及初始低正则性会引起何种降阶？
- 如何结合有限元得到全离散误差估计？

## 拟研究的目标（须注明条件）
对于适当的非线性抛物型 PDE，考察 ||u(t_n)-u_h^n|| <= C (tau^2 + h^(r+1))，其中 C 不依赖 tau、h；这只是研究目标，并非对所有模型均成立的定理。
