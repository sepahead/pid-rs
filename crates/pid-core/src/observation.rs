//! Typed provenance for software-added Gaussian noise.
//!
//! # Method provenance and availability
//!
//! **PROJECT-DEFINED SCIENTIFIC SOFTWARE CONTRACT.** The types in this module separate an ideal
//! population kernel, a caller declaration, a deterministic floating-point application, and the
//! resulting matrix identities. The contract is new in pid-rs. It is not a new PID estimator or a
//! claim of mathematical novelty.
//!
//! Method catalog: preprocessing.gaussian-noise-provenance
//!
//! # Mathematical boundary
//!
//! The declared ideal model is
//!
//! `Y = X + Z`, where `Z ~ N(0, sigma^2 I)` is independent of `X` and `sigma > 0`.
//!
//! If that population declaration is true for every joint coordinate, convolution with the
//! nondegenerate Gaussian kernel gives the law of `Y` a strictly positive, smooth density with
//! full Euclidean support. This result does not prove that rows are independent and identically
//! distributed. It also does not prove finite mutual information, KSG consistency, calibrated
//! uncertainty, or any monotonic behavior of PID atoms.
//!
//! One declaration covers one matrix. Separate declarations for sources and a target do not
//! establish a joint population-noise model or mutual independence across applications. A
//! full-support conclusion for concatenated KSG or PID inputs needs one justified joint model for
//! all source and target coordinates. This module does not yet provide that higher-level report.
//!
//! The generated matrix is not itself a continuous probability law. It is one deterministic,
//! binary64, pseudorandom approximation to a draw from the declared kernel. The generator uses
//! non-cryptographic SplitMix64 and platform floating-point elementary functions. Exact replay
//! therefore requires the same pid-rs algorithm and compatible floating-point behavior.
//!
//! A zero-noise comparison is not a Gaussian model with `sigma = 0`. This module rejects zero.
//! A future sensitivity-trajectory report must bind an unmodified comparison, the scale grid, and
//! the coupling policy as one object.

use std::fmt;

use serde::Serialize;
use sha2::{Digest, Sha256};

use crate::error::{PidError, PidResult};
use crate::matrix::{MatOwned, MatRef};
use crate::preprocess::Jitter;
use crate::resource::{try_vec_with_capacity, CancellationToken, ResourceBudget, ResourceEstimate};

const CONTRACT_REVISION: u32 = 1;
const MAX_RATIONALE_BYTES: usize = 4 * 1024;
const MODEL_IDENTITY_DOMAIN: &[u8] = b"pid-rs/gaussian-noise/model/v1\0";
const DECLARATION_IDENTITY_DOMAIN: &[u8] = b"pid-rs/gaussian-noise/declaration/v1\0";
const STREAM_IDENTITY_DOMAIN: &[u8] = b"pid-rs/gaussian-noise/stream/v1\0";
const EFFECTIVE_SEED_DOMAIN: &[u8] = b"pid-rs/gaussian-noise/effective-seed/v1\0";
const MATRIX_IDENTITY_DOMAIN: &[u8] = b"pid-rs/matrix/row-major-f64-bits-le/v1\0";
const APPLICATION_IDENTITY_DOMAIN: &[u8] = b"pid-rs/gaussian-noise/application/v1\0";
const OPERATION: &str = "GaussianNoiseTransform::apply";

fn update_bytes(digest: &mut Sha256, value: &[u8]) {
    digest.update((value.len() as u128).to_le_bytes());
    digest.update(value);
}

fn copy_rationale(value: &str, budget: ResourceBudget) -> PidResult<String> {
    if value.trim().is_empty() {
        return Err(PidError::InvalidConfig {
            context: "GaussianNoiseDeclaration::new",
            message: "rationale must be nonempty",
        });
    }
    if value.len() > MAX_RATIONALE_BYTES {
        return Err(PidError::ResourceLimitExceeded {
            operation: "GaussianNoiseDeclaration::new",
            resource: "rationale_bytes",
            requested: value.len() as u128,
            limit: MAX_RATIONALE_BYTES as u128,
        });
    }
    if value.chars().any(char::is_control) {
        return Err(PidError::InvalidConfig {
            context: "GaussianNoiseDeclaration::new",
            message: "rationale must not contain control characters",
        });
    }
    let mut bytes = try_vec_with_capacity(
        "GaussianNoiseDeclaration::new rationale",
        value.len(),
        budget,
    )?;
    bytes.extend_from_slice(value.as_bytes());
    String::from_utf8(bytes).map_err(|_| PidError::InvalidConfig {
        context: "GaussianNoiseDeclaration::new",
        message: "rationale must be valid UTF-8",
    })
}

/// Mathematical law declared for the added noise.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseLaw {
    /// Zero-mean additive Gaussian noise in the ideal population model.
    ZeroMeanAdditiveGaussian,
}

/// Units and preprocessing state in which the scalar standard deviation is interpreted.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseScaleReference {
    /// The caller declares that all matrix columns use one common input unit and calibration.
    /// The digest identifies that declared unit contract; it does not prove the declaration.
    DeclaredCommonInputUnits { unit_identity_sha256: [u8; 32] },
    /// The caller declares common output units after one fixed preprocessing operation.
    ///
    /// The preprocessing and output-unit identities define the population-level coordinate
    /// system. The declaration separately binds the exact finite preprocessing output.
    DeclaredAfterFixedPreprocessing {
        preprocessing_identity_sha256: [u8; 32],
        output_unit_identity_sha256: [u8; 32],
    },
}

impl GaussianNoiseScaleReference {
    fn update_identity(self, digest: &mut Sha256) {
        match self {
            Self::DeclaredCommonInputUnits {
                unit_identity_sha256,
            } => {
                update_bytes(digest, b"declared_common_input_units");
                digest.update(unit_identity_sha256);
            }
            Self::DeclaredAfterFixedPreprocessing {
                preprocessing_identity_sha256,
                output_unit_identity_sha256,
            } => {
                update_bytes(digest, b"declared_after_fixed_preprocessing");
                digest.update(preprocessing_identity_sha256);
                digest.update(output_unit_identity_sha256);
            }
        }
    }
}

/// Exact finite-input binding attached to one scientific declaration.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseInputBinding {
    /// The generated application report binds the exact input matrix. No fitted preprocessing is
    /// declared at this layer.
    ApplicationInputOnly,
    /// The exact supplied matrix must be the output of the fixed preprocessing identity in the
    /// population-kernel specification.
    ExactFixedPreprocessingOutput {
        preprocessing_output_matrix_sha256: [u8; 32],
    },
}

impl GaussianNoiseInputBinding {
    fn update_identity(self, digest: &mut Sha256) {
        match self {
            Self::ApplicationInputOnly => update_bytes(digest, b"application_input_only"),
            Self::ExactFixedPreprocessingOutput {
                preprocessing_output_matrix_sha256,
            } => {
                update_bytes(digest, b"exact_fixed_preprocessing_output");
                digest.update(preprocessing_output_matrix_sha256);
            }
        }
    }

    fn validate_input_identity(self, input_identity_sha256: [u8; 32]) -> PidResult<()> {
        if let Self::ExactFixedPreprocessingOutput {
            preprocessing_output_matrix_sha256,
        } = self
        {
            if preprocessing_output_matrix_sha256 != input_identity_sha256 {
                return Err(PidError::InvalidConfig {
                    context: OPERATION,
                    message:
                        "input matrix does not match the declared preprocessing output identity",
                });
            }
        }
        Ok(())
    }
}

/// Coordinate scope of the ideal noise kernel.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseCoordinateScope {
    /// The model adds noise to every cell of the input matrix.
    AllMatrixCells,
}

/// Dependence declaration for the ideal noise kernel.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseDependence {
    /// Ideal noise variables are independent across all rows and columns and independent of the
    /// input random vector. This is a caller declaration, not a property proved from a seed.
    IndependentAcrossMatrixCellsAndInput,
}

/// Population-kernel specification. Its identity never contains a seed or finite realization.
#[derive(Debug, Clone, Copy, PartialEq, Serialize)]
#[non_exhaustive]
pub struct GaussianNoiseSpecification {
    contract_revision: u32,
    law: GaussianNoiseLaw,
    standard_deviation: f64,
    scale_reference: GaussianNoiseScaleReference,
    coordinate_scope: GaussianNoiseCoordinateScope,
    dependence: GaussianNoiseDependence,
    model_identity_sha256: [u8; 32],
}

impl GaussianNoiseSpecification {
    /// Construct a nondegenerate scalar Gaussian kernel for every matrix cell.
    pub fn new(
        standard_deviation: f64,
        scale_reference: GaussianNoiseScaleReference,
    ) -> PidResult<Self> {
        if !standard_deviation.is_finite() || standard_deviation <= 0.0 {
            return Err(PidError::InvalidConfig {
                context: "GaussianNoiseSpecification::new",
                message: "standard_deviation must be finite and > 0",
            });
        }
        let law = GaussianNoiseLaw::ZeroMeanAdditiveGaussian;
        let coordinate_scope = GaussianNoiseCoordinateScope::AllMatrixCells;
        let dependence = GaussianNoiseDependence::IndependentAcrossMatrixCellsAndInput;
        let mut digest = Sha256::new();
        digest.update(MODEL_IDENTITY_DOMAIN);
        digest.update(CONTRACT_REVISION.to_le_bytes());
        update_bytes(&mut digest, b"zero_mean_additive_gaussian");
        digest.update(standard_deviation.to_bits().to_le_bytes());
        scale_reference.update_identity(&mut digest);
        update_bytes(&mut digest, b"all_matrix_cells");
        update_bytes(&mut digest, b"independent_across_matrix_cells_and_input");
        Ok(Self {
            contract_revision: CONTRACT_REVISION,
            law,
            standard_deviation,
            scale_reference,
            coordinate_scope,
            dependence,
            model_identity_sha256: digest.finalize().into(),
        })
    }

    pub fn contract_revision(&self) -> u32 {
        self.contract_revision
    }

    pub fn law(&self) -> GaussianNoiseLaw {
        self.law
    }

    pub fn standard_deviation(&self) -> f64 {
        self.standard_deviation
    }

    pub fn scale_reference(&self) -> GaussianNoiseScaleReference {
        self.scale_reference
    }

    pub fn coordinate_scope(&self) -> GaussianNoiseCoordinateScope {
        self.coordinate_scope
    }

    pub fn dependence(&self) -> GaussianNoiseDependence {
        self.dependence
    }

    /// Identity of the ideal population kernel. Seeds and realized matrices are excluded.
    pub fn model_identity_sha256(&self) -> [u8; 32] {
        self.model_identity_sha256
    }
}

/// Coupling policy for one declared noise-scale sensitivity study.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseSensitivityCoupling {
    /// Every scale uses the same underlying standard-normal pseudodraws. Sigma is deliberately
    /// absent from stream derivation.
    CommonStandardNormalDrawsAcrossScales,
    /// Each scale uses a separate deterministic pseudodraw stream. This does not claim
    /// probabilistic or cryptographic independence.
    SeparatePseudodrawStreamsAcrossScales,
}

/// Scientific purpose of one Gaussian-noise application.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoisePurpose {
    /// The caller declares that the Gaussian kernel is part of the population observation model.
    DeclaredObservationModel,
    /// One probe in a named, seeded scale-sensitivity study.
    ///
    /// One probe does not establish a sensitivity result and must not clear a
    /// `ObservationNoiseSensitivityNotEvaluated` warning by itself.
    SeededScaleSensitivityProbe {
        study_identity_sha256: [u8; 32],
        coupling: GaussianNoiseSensitivityCoupling,
    },
}

impl GaussianNoisePurpose {
    fn update_identity(self, digest: &mut Sha256) {
        match self {
            Self::DeclaredObservationModel => {
                update_bytes(digest, b"declared_observation_model");
            }
            Self::SeededScaleSensitivityProbe {
                study_identity_sha256,
                coupling,
            } => {
                update_bytes(digest, b"seeded_scale_sensitivity_probe");
                digest.update(study_identity_sha256);
                update_bytes(
                    digest,
                    match coupling {
                        GaussianNoiseSensitivityCoupling::CommonStandardNormalDrawsAcrossScales => {
                            b"common_standard_normal_draws_across_scales"
                        }
                        GaussianNoiseSensitivityCoupling::SeparatePseudodrawStreamsAcrossScales => {
                            b"separate_pseudodraw_streams_across_scales"
                        }
                    },
                );
            }
        }
    }
}

/// Checked scientific declaration that wraps one Gaussian kernel specification.
#[derive(Debug, PartialEq, Serialize)]
#[non_exhaustive]
pub struct GaussianNoiseDeclaration {
    contract_revision: u32,
    specification: GaussianNoiseSpecification,
    purpose: GaussianNoisePurpose,
    input_binding: GaussianNoiseInputBinding,
    rationale: String,
    declaration_identity_sha256: [u8; 32],
}

impl GaussianNoiseDeclaration {
    pub fn new(
        specification: GaussianNoiseSpecification,
        purpose: GaussianNoisePurpose,
        input_binding: GaussianNoiseInputBinding,
        rationale: impl AsRef<str>,
    ) -> PidResult<Self> {
        Self::new_with_budget(
            specification,
            purpose,
            input_binding,
            rationale,
            ResourceBudget::default(),
        )
    }

    pub fn new_with_budget(
        specification: GaussianNoiseSpecification,
        purpose: GaussianNoisePurpose,
        input_binding: GaussianNoiseInputBinding,
        rationale: impl AsRef<str>,
        budget: ResourceBudget,
    ) -> PidResult<Self> {
        budget.validate("GaussianNoiseDeclaration::new")?;
        match (specification.scale_reference, input_binding) {
            (
                GaussianNoiseScaleReference::DeclaredCommonInputUnits { .. },
                GaussianNoiseInputBinding::ApplicationInputOnly,
            )
            | (
                GaussianNoiseScaleReference::DeclaredAfterFixedPreprocessing { .. },
                GaussianNoiseInputBinding::ExactFixedPreprocessingOutput { .. },
            ) => {}
            _ => {
                return Err(PidError::InvalidConfig {
                    context: "GaussianNoiseDeclaration::new",
                    message: "input binding must match the scale-reference kind",
                });
            }
        }
        let rationale = copy_rationale(rationale.as_ref(), budget)?;
        let mut digest = Sha256::new();
        digest.update(DECLARATION_IDENTITY_DOMAIN);
        digest.update(CONTRACT_REVISION.to_le_bytes());
        digest.update(specification.model_identity_sha256());
        purpose.update_identity(&mut digest);
        input_binding.update_identity(&mut digest);
        update_bytes(&mut digest, rationale.as_bytes());
        Ok(Self {
            contract_revision: CONTRACT_REVISION,
            specification,
            purpose,
            input_binding,
            rationale,
            declaration_identity_sha256: digest.finalize().into(),
        })
    }

    /// Fallibly copy the bounded rationale under an explicit resource ceiling.
    pub fn try_clone_with_budget(&self, budget: ResourceBudget) -> PidResult<Self> {
        Self::new_with_budget(
            self.specification,
            self.purpose,
            self.input_binding,
            &self.rationale,
            budget,
        )
    }

    pub fn contract_revision(&self) -> u32 {
        self.contract_revision
    }

    pub fn specification(&self) -> GaussianNoiseSpecification {
        self.specification
    }

    pub fn purpose(&self) -> GaussianNoisePurpose {
        self.purpose
    }

    pub fn input_binding(&self) -> GaussianNoiseInputBinding {
        self.input_binding
    }

    pub fn rationale(&self) -> &str {
        &self.rationale
    }

    /// Identity of the kernel, purpose, finite-input binding, and exact rationale bytes. It
    /// excludes all seeds and generated output matrices.
    pub fn declaration_identity_sha256(&self) -> [u8; 32] {
        self.declaration_identity_sha256
    }
}

/// Caller declaration about how all stream-identity inputs were selected.
///
/// The declaration covers the base seed, logical-matrix identity, and stream-domain identity.
/// Each input must satisfy the selected rule. A fixed base seed does not make a stream independent
/// of evaluation values if either identity was derived from those values.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseStreamSelection {
    /// All stream-identity inputs were fixed before inspection of the evaluation data.
    FixedBeforeEvaluationDataInspection,
    /// All stream-identity inputs were selected without using the evaluation data. The code does
    /// not verify this caller declaration.
    SelectedWithoutEvaluationDataDependence,
}

impl GaussianNoiseStreamSelection {
    fn tag(self) -> &'static [u8] {
        match self {
            Self::FixedBeforeEvaluationDataInspection => b"fixed_before_evaluation_data_inspection",
            Self::SelectedWithoutEvaluationDataDependence => {
                b"selected_without_evaluation_data_dependence"
            }
        }
    }
}

/// Stream declaration for one logical matrix and workflow domain.
///
/// The transform derives the effective 64-bit generator seed from this object, the application
/// context, and the declared purpose. A common-draw scale study excludes the standard deviation.
/// A separate-stream scale study includes only the standard-deviation bits, not data identities.
#[derive(Clone, Copy, PartialEq, Eq, Serialize)]
#[non_exhaustive]
pub struct GaussianNoiseStream {
    contract_revision: u32,
    base_seed: u64,
    stream_selection: GaussianNoiseStreamSelection,
    logical_matrix_identity_sha256: [u8; 32],
    stream_domain_identity_sha256: [u8; 32],
    stream_identity_sha256: [u8; 32],
}

impl fmt::Debug for GaussianNoiseStream {
    fn fmt(&self, formatter: &mut fmt::Formatter<'_>) -> fmt::Result {
        formatter
            .debug_struct("GaussianNoiseStream")
            .field("contract_revision", &self.contract_revision)
            .field("base_seed", &"<redacted; available by explicit accessor>")
            .field("stream_selection", &self.stream_selection)
            .field(
                "logical_matrix_identity_sha256",
                &self.logical_matrix_identity_sha256,
            )
            .field(
                "stream_domain_identity_sha256",
                &self.stream_domain_identity_sha256,
            )
            .field("stream_identity_sha256", &self.stream_identity_sha256)
            .finish()
    }
}

impl GaussianNoiseStream {
    pub fn new(
        base_seed: u64,
        stream_selection: GaussianNoiseStreamSelection,
        logical_matrix_identity_sha256: [u8; 32],
        stream_domain_identity_sha256: [u8; 32],
    ) -> Self {
        let mut digest = Sha256::new();
        digest.update(STREAM_IDENTITY_DOMAIN);
        digest.update(CONTRACT_REVISION.to_le_bytes());
        digest.update(base_seed.to_le_bytes());
        update_bytes(&mut digest, stream_selection.tag());
        digest.update(logical_matrix_identity_sha256);
        digest.update(stream_domain_identity_sha256);
        Self {
            contract_revision: CONTRACT_REVISION,
            base_seed,
            stream_selection,
            logical_matrix_identity_sha256,
            stream_domain_identity_sha256,
            stream_identity_sha256: digest.finalize().into(),
        }
    }

    pub fn contract_revision(&self) -> u32 {
        self.contract_revision
    }

    /// Base seed. The effective generator seed also binds the matrix, stream domain, and context.
    pub fn base_seed(&self) -> u64 {
        self.base_seed
    }

    pub fn stream_selection(&self) -> GaussianNoiseStreamSelection {
        self.stream_selection
    }

    pub fn logical_matrix_identity_sha256(&self) -> [u8; 32] {
        self.logical_matrix_identity_sha256
    }

    pub fn stream_domain_identity_sha256(&self) -> [u8; 32] {
        self.stream_domain_identity_sha256
    }

    pub fn stream_identity_sha256(&self) -> [u8; 32] {
        self.stream_identity_sha256
    }
}

/// Caller-declared position of the supplied matrix in a larger workflow.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(tag = "kind", rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseApplicationContext {
    /// Apply noise directly to the supplied matrix. The matrix may already be preprocessed.
    DirectInput,
    /// The caller declares that the input follows one ordered row-resampling operation.
    ///
    /// The report binds this digest and the exact input matrix as separate facts. It does not
    /// prove that the declared indices produced that matrix.
    AfterDeclaredRowResampling {
        declared_resample_indices_hash_sha256: [u8; 32],
    },
}

impl GaussianNoiseApplicationContext {
    fn update_identity(self, digest: &mut Sha256) {
        match self {
            Self::DirectInput => update_bytes(digest, b"direct_input"),
            Self::AfterDeclaredRowResampling {
                declared_resample_indices_hash_sha256,
            } => {
                update_bytes(digest, b"after_declared_row_resampling");
                digest.update(declared_resample_indices_hash_sha256);
            }
        }
    }
}

/// Exact generator and traversal revision used by pid-rs.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseGeneratorRevision {
    /// SplitMix64 state transition and finalizer; high-53-bit `[0,1)` conversion; redraw of an
    /// exact zero radial uniform; Box--Muller radius and cosine branch; no cached sine value; one
    /// generated value for each cell in serial row-major order.
    SplitMix64BoxMullerCosineNoCacheRowMajorV1,
}

impl GaussianNoiseGeneratorRevision {
    fn tag(self) -> &'static [u8] {
        match self {
            Self::SplitMix64BoxMullerCosineNoCacheRowMajorV1 => {
                b"splitmix64_box_muller_cosine_no_cache_row_major_v1"
            }
        }
    }
}

/// Security scope of the generator and recorded hashes.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseSecurityScope {
    /// The generator is non-cryptographic. Seeds and unsalted data hashes provide no
    /// confidentiality, authenticity, or attestation.
    NonCryptographicNoConfidentialityOrAuthenticity,
}

/// Exact-replay boundary for the floating-point generator.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseReplayScope {
    /// Exact replay requires the same algorithm and compatible binary64 elementary-function
    /// behavior. Cross-platform bit identity is not claimed.
    MatchingAlgorithmAndFloatingPointEnvironment,
}

/// Scientific claim boundary attached to each generated report.
#[derive(Debug, Clone, Copy, PartialEq, Eq, Serialize)]
#[serde(rename_all = "snake_case")]
#[non_exhaustive]
pub enum GaussianNoiseScientificClaimBoundary {
    /// Smooth positive density and full support are conditional conclusions about the declared
    /// ideal population law only. They are not properties of the fixed pseudorandom array. The
    /// declaration does not establish finite MI, iid rows, estimator validity, or PID-atom
    /// monotonicity. Separate reports also do not establish a joint noise model across matrices.
    IdealPopulationLawOnlyV1,
}

/// Consumed application plan. Only [`Self::apply`] can construct a generated report.
#[derive(Debug)]
pub struct GaussianNoiseTransform {
    declaration: GaussianNoiseDeclaration,
    stream: GaussianNoiseStream,
}

impl GaussianNoiseTransform {
    pub fn new(declaration: GaussianNoiseDeclaration, stream: GaussianNoiseStream) -> Self {
        Self {
            declaration,
            stream,
        }
    }

    pub fn declaration(&self) -> &GaussianNoiseDeclaration {
        &self.declaration
    }

    pub fn stream(&self) -> GaussianNoiseStream {
        self.stream
    }

    /// Estimate output, changed-count, hashing, and generator work.
    pub fn resource_estimate(input: MatRef<'_>) -> PidResult<ResourceEstimate> {
        if input.nrows() == 0 || input.ncols() == 0 {
            return Err(PidError::InvalidConfig {
                context: OPERATION,
                message: "input must contain at least one row and one column",
            });
        }
        let values = input
            .nrows()
            .checked_mul(input.ncols())
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let output_bytes = (values as u128)
            .checked_mul(std::mem::size_of::<f64>() as u128)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        let count_bytes = (input.ncols() as u128)
            .checked_mul(std::mem::size_of::<usize>() as u128)
            .ok_or(PidError::SizeOverflow {
                operation: OPERATION,
            })?;
        Ok(ResourceEstimate {
            estimated_bytes: output_bytes.checked_add(count_bytes).ok_or(
                PidError::SizeOverflow {
                    operation: OPERATION,
                },
            )?,
            pairwise_distances: 0,
            // Input hash, generation, change accounting, output hash, and application identity.
            operations_hint: (values as u128)
                .checked_mul(5)
                .and_then(|work| work.checked_add(input.ncols() as u128))
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?,
        })
    }

    pub fn apply(
        self,
        input: MatRef<'_>,
        context: GaussianNoiseApplicationContext,
    ) -> PidResult<GaussianNoiseApplicationResult> {
        self.apply_with_budget(input, context, ResourceBudget::default())
    }

    pub fn apply_with_budget(
        self,
        input: MatRef<'_>,
        context: GaussianNoiseApplicationContext,
        budget: ResourceBudget,
    ) -> PidResult<GaussianNoiseApplicationResult> {
        let cancellation = CancellationToken::new();
        self.apply_with_budget_and_cancellation(input, context, budget, &cancellation)
    }

    pub fn apply_with_budget_and_cancellation(
        self,
        input: MatRef<'_>,
        context: GaussianNoiseApplicationContext,
        budget: ResourceBudget,
        cancellation: &CancellationToken,
    ) -> PidResult<GaussianNoiseApplicationResult> {
        budget.check(OPERATION, Self::resource_estimate(input)?)?;
        let input_matrix_identity_sha256 =
            matrix_identity_with_cancellation(input, cancellation, OPERATION)?;
        self.declaration
            .input_binding
            .validate_input_identity(input_matrix_identity_sha256)?;
        let effective_seed = effective_seed(self.stream, context, &self.declaration);
        let jitter = Jitter::new(
            self.declaration.specification.standard_deviation,
            effective_seed,
        )?;
        let (matrix, bitwise_changed_values_per_column) = jitter
            .apply_with_budget_and_cancellation(input, budget, cancellation, true, OPERATION)?;
        let bitwise_changed_elements =
            bitwise_changed_values_per_column
                .iter()
                .try_fold(0usize, |total, &count| {
                    total.checked_add(count).ok_or(PidError::SizeOverflow {
                        operation: OPERATION,
                    })
                })?;
        let element_count =
            input
                .nrows()
                .checked_mul(input.ncols())
                .ok_or(PidError::SizeOverflow {
                    operation: OPERATION,
                })?;
        let bitwise_unchanged_elements = element_count
            .checked_sub(bitwise_changed_elements)
            .ok_or(PidError::NumericalInstability {
                context: "GaussianNoiseTransform::apply changed-count invariant",
            })?;
        if bitwise_changed_elements == 0 {
            return Err(PidError::NumericalInstability {
                context: "GaussianNoiseTransform::apply produced no bitwise change; use an explicit unmodified comparison or a representable positive scale",
            });
        }
        let output_matrix_identity_sha256 =
            matrix_identity_with_cancellation(matrix.as_ref(), cancellation, OPERATION)?;
        let generator_revision =
            GaussianNoiseGeneratorRevision::SplitMix64BoxMullerCosineNoCacheRowMajorV1;
        let security_scope =
            GaussianNoiseSecurityScope::NonCryptographicNoConfidentialityOrAuthenticity;
        let replay_scope = GaussianNoiseReplayScope::MatchingAlgorithmAndFloatingPointEnvironment;
        let scientific_claim_boundary =
            GaussianNoiseScientificClaimBoundary::IdealPopulationLawOnlyV1;
        let application_identity_sha256 = application_identity(
            &self.declaration,
            self.stream,
            context,
            generator_revision,
            effective_seed,
            input.nrows(),
            input.ncols(),
            input_matrix_identity_sha256,
            output_matrix_identity_sha256,
            &bitwise_changed_values_per_column,
        );
        let report = GaussianNoiseApplicationReport {
            contract_revision: CONTRACT_REVISION,
            declaration: self.declaration,
            stream: self.stream,
            context,
            generator_revision,
            effective_seed,
            rows: input.nrows(),
            columns: input.ncols(),
            input_matrix_identity_sha256,
            output_matrix_identity_sha256,
            bitwise_changed_values_per_column,
            bitwise_changed_elements,
            bitwise_unchanged_elements,
            changes_estimand: true,
            security_scope,
            replay_scope,
            scientific_claim_boundary,
            application_identity_sha256,
        };
        Ok(GaussianNoiseApplicationResult { matrix, report })
    }
}

fn effective_seed(
    stream: GaussianNoiseStream,
    context: GaussianNoiseApplicationContext,
    declaration: &GaussianNoiseDeclaration,
) -> u64 {
    let mut digest = Sha256::new();
    digest.update(EFFECTIVE_SEED_DOMAIN);
    digest.update(CONTRACT_REVISION.to_le_bytes());
    digest.update(stream.stream_identity_sha256);
    context.update_identity(&mut digest);
    match declaration.purpose {
        GaussianNoisePurpose::DeclaredObservationModel => {
            update_bytes(&mut digest, b"declared_observation_model");
        }
        GaussianNoisePurpose::SeededScaleSensitivityProbe {
            study_identity_sha256,
            coupling: GaussianNoiseSensitivityCoupling::CommonStandardNormalDrawsAcrossScales,
        } => {
            update_bytes(
                &mut digest,
                b"scale_sensitivity_common_standard_normal_draws",
            );
            digest.update(study_identity_sha256);
        }
        GaussianNoisePurpose::SeededScaleSensitivityProbe {
            study_identity_sha256,
            coupling: GaussianNoiseSensitivityCoupling::SeparatePseudodrawStreamsAcrossScales,
        } => {
            update_bytes(
                &mut digest,
                b"scale_sensitivity_separate_pseudodraw_streams",
            );
            digest.update(study_identity_sha256);
            digest.update(
                declaration
                    .specification
                    .standard_deviation
                    .to_bits()
                    .to_le_bytes(),
            );
        }
    }
    let bytes: [u8; 32] = digest.finalize().into();
    u64::from_le_bytes([
        bytes[0], bytes[1], bytes[2], bytes[3], bytes[4], bytes[5], bytes[6], bytes[7],
    ])
}

#[allow(clippy::too_many_arguments)]
fn application_identity(
    declaration: &GaussianNoiseDeclaration,
    stream: GaussianNoiseStream,
    context: GaussianNoiseApplicationContext,
    generator_revision: GaussianNoiseGeneratorRevision,
    effective_seed: u64,
    rows: usize,
    columns: usize,
    input_matrix_identity_sha256: [u8; 32],
    output_matrix_identity_sha256: [u8; 32],
    bitwise_changed_values_per_column: &[usize],
) -> [u8; 32] {
    let mut digest = Sha256::new();
    digest.update(APPLICATION_IDENTITY_DOMAIN);
    digest.update(CONTRACT_REVISION.to_le_bytes());
    digest.update(declaration.declaration_identity_sha256);
    digest.update(stream.stream_identity_sha256);
    context.update_identity(&mut digest);
    update_bytes(&mut digest, generator_revision.tag());
    digest.update(effective_seed.to_le_bytes());
    digest.update((rows as u128).to_le_bytes());
    digest.update((columns as u128).to_le_bytes());
    digest.update(input_matrix_identity_sha256);
    digest.update(output_matrix_identity_sha256);
    digest.update((bitwise_changed_values_per_column.len() as u128).to_le_bytes());
    for &count in bitwise_changed_values_per_column {
        digest.update((count as u128).to_le_bytes());
    }
    digest.finalize().into()
}

/// Generated application report. All fields are private and only the transform can construct it.
#[derive(Debug, Serialize)]
#[non_exhaustive]
pub struct GaussianNoiseApplicationReport {
    contract_revision: u32,
    declaration: GaussianNoiseDeclaration,
    stream: GaussianNoiseStream,
    context: GaussianNoiseApplicationContext,
    generator_revision: GaussianNoiseGeneratorRevision,
    effective_seed: u64,
    rows: usize,
    columns: usize,
    input_matrix_identity_sha256: [u8; 32],
    output_matrix_identity_sha256: [u8; 32],
    bitwise_changed_values_per_column: Vec<usize>,
    bitwise_changed_elements: usize,
    bitwise_unchanged_elements: usize,
    changes_estimand: bool,
    security_scope: GaussianNoiseSecurityScope,
    replay_scope: GaussianNoiseReplayScope,
    scientific_claim_boundary: GaussianNoiseScientificClaimBoundary,
    application_identity_sha256: [u8; 32],
}

impl GaussianNoiseApplicationReport {
    pub fn contract_revision(&self) -> u32 {
        self.contract_revision
    }

    pub fn declaration(&self) -> &GaussianNoiseDeclaration {
        &self.declaration
    }

    pub fn stream(&self) -> GaussianNoiseStream {
        self.stream
    }

    pub fn context(&self) -> GaussianNoiseApplicationContext {
        self.context
    }

    pub fn generator_revision(&self) -> GaussianNoiseGeneratorRevision {
        self.generator_revision
    }

    /// Effective seed after binding the logical matrix, stream domain, and application context.
    pub fn effective_seed(&self) -> u64 {
        self.effective_seed
    }

    pub fn rows(&self) -> usize {
        self.rows
    }

    pub fn columns(&self) -> usize {
        self.columns
    }

    pub fn input_matrix_identity_sha256(&self) -> [u8; 32] {
        self.input_matrix_identity_sha256
    }

    pub fn output_matrix_identity_sha256(&self) -> [u8; 32] {
        self.output_matrix_identity_sha256
    }

    pub fn bitwise_changed_values_per_column(&self) -> &[usize] {
        &self.bitwise_changed_values_per_column
    }

    pub fn bitwise_changed_elements(&self) -> usize {
        self.bitwise_changed_elements
    }

    pub fn bitwise_unchanged_elements(&self) -> usize {
        self.bitwise_unchanged_elements
    }

    /// Added noise changes the declared population estimand. This is not a claim that every
    /// binary64 cell changed after rounding.
    pub fn changes_estimand(&self) -> bool {
        self.changes_estimand
    }

    pub fn security_scope(&self) -> GaussianNoiseSecurityScope {
        self.security_scope
    }

    pub fn replay_scope(&self) -> GaussianNoiseReplayScope {
        self.replay_scope
    }

    pub fn scientific_claim_boundary(&self) -> GaussianNoiseScientificClaimBoundary {
        self.scientific_claim_boundary
    }

    pub fn application_identity_sha256(&self) -> [u8; 32] {
        self.application_identity_sha256
    }

    pub fn verifies_input_matrix(&self, matrix: MatRef<'_>) -> PidResult<bool> {
        Ok(self.rows == matrix.nrows()
            && self.columns == matrix.ncols()
            && observation_noise_matrix_identity(matrix)? == self.input_matrix_identity_sha256)
    }

    pub fn verifies_output_matrix(&self, matrix: MatRef<'_>) -> PidResult<bool> {
        Ok(self.rows == matrix.nrows()
            && self.columns == matrix.ncols()
            && observation_noise_matrix_identity(matrix)? == self.output_matrix_identity_sha256)
    }
}

/// Immutable transformed matrix plus its generated application report.
#[derive(Debug)]
pub struct GaussianNoiseApplicationResult {
    matrix: MatOwned,
    report: GaussianNoiseApplicationReport,
}

impl GaussianNoiseApplicationResult {
    pub fn matrix(&self) -> MatRef<'_> {
        self.matrix.as_ref()
    }

    pub fn report(&self) -> &GaussianNoiseApplicationReport {
        &self.report
    }

    pub fn into_parts(self) -> (MatOwned, GaussianNoiseApplicationReport) {
        (self.matrix, self.report)
    }
}

/// SHA-256 identity of matrix shape, row-major order, and exact binary64 bits in the versioned
/// observation-noise matrix domain.
pub fn observation_noise_matrix_identity(matrix: MatRef<'_>) -> PidResult<[u8; 32]> {
    let cancellation = CancellationToken::new();
    matrix_identity_with_cancellation(matrix, &cancellation, "observation noise matrix identity")
}

fn matrix_identity_with_cancellation(
    matrix: MatRef<'_>,
    cancellation: &CancellationToken,
    operation: &'static str,
) -> PidResult<[u8; 32]> {
    let total = matrix
        .nrows()
        .checked_mul(matrix.ncols())
        .ok_or(PidError::SizeOverflow { operation })?;
    let mut digest = Sha256::new();
    digest.update(MATRIX_IDENTITY_DOMAIN);
    digest.update((matrix.nrows() as u128).to_le_bytes());
    digest.update((matrix.ncols() as u128).to_le_bytes());
    cancellation.check(operation, 0, total)?;
    for (index, value) in matrix.as_slice().iter().enumerate() {
        digest.update(value.to_bits().to_le_bytes());
        let completed = index + 1;
        if completed.is_multiple_of(1_024) {
            cancellation.check(operation, completed, total)?;
        }
    }
    cancellation.check(operation, total, total)?;
    Ok(digest.finalize().into())
}
